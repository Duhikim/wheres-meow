import pytest

from fakes import FakeClock, FakeGameEventPublisher, FakeGameResultRecorder, FakeTurnTimer
from wheresmeow.game.adapter.outbound.memory.in_memory_game_store import InMemoryGameStore
from wheresmeow.game.application.port.inbound import GamePlayer
from wheresmeow.game.application.service.game_service import GameService
from wheresmeow.game.application.service.rematch_service import RematchService
from wheresmeow.game.domain.board import FixedMineLayoutGenerator
from wheresmeow.game.domain.errors import AlreadyInGame, RematchExpired
from wheresmeow.game.domain.game import GameMode, GameStatus
from wheresmeow.game.domain.rematch import REMATCH_WINDOW_MS
from wheresmeow.game.domain.skins import SkinPreference
from wheresmeow.shared.errors import InvalidInput

CATS = {(x, y) for y in range(10, 12) for x in range(0, 12)} | {(11, 9)}
HOST = GamePlayer("host", "방장", SkinPreference(16, 17))
GUEST = GamePlayer("guest", "손님", SkinPreference(16, 20))


class FakeRematchNotifier:
    def __init__(self) -> None:
        self.requested: list[tuple[str, str]] = []
        self.cancelled: list[tuple[str, str, str]] = []

    def rematch_requested(self, game_id: str, to_player_id: str) -> None:
        self.requested.append((game_id, to_player_id))

    def rematch_cancelled(self, game_id: str, to_player_ids: list[str], reason: str) -> None:
        for player_id in to_player_ids:
            self.cancelled.append((game_id, player_id, reason))


class Env:
    def __init__(self) -> None:
        self.clock = FakeClock(now_ms=0)
        self.timer = FakeTurnTimer()
        self.publisher = FakeGameEventPublisher()
        ids = iter(f"g{n}" for n in range(1, 100))
        self.games = GameService(
            InMemoryGameStore(), self.publisher, self.timer, FixedMineLayoutGenerator(CATS), self.clock,
            recorder=FakeGameResultRecorder(), first_seat_chooser=lambda: 0, id_factory=lambda: next(ids),
        )
        self.notifier = FakeRematchNotifier()
        self.rematches = RematchService(self.games, self.notifier, self.timer, self.clock)

    def finished_game(self, mode: GameMode = GameMode.INVITE) -> str:
        game = self.games.start_game(mode, HOST, GUEST)
        self.games.forfeit(game.id, "guest")
        return game.id


class TestGameServiceStartRematch:
    class TestStartRematch:
        def test_성공_같은_좌석_같은_스킨_같은_모드로_선공만_바꿔_시작한다(self):
            env = Env()
            previous = env.games.get_game(env.finished_game(GameMode.MATCH), "host")

            game = env.games.start_rematch(previous)

            assert game.id != previous.id and game.status is GameStatus.IN_PROGRESS
            assert [(s.player_id, s.skin) for s in game.seats] == [(s.player_id, s.skin) for s in previous.seats]
            assert game.mode is GameMode.MATCH
            assert (previous.first_seat, game.first_seat, game.current_seat) == (0, 1, 1)
            assert all(s.score == 0 for s in game.seats)

        def test_실패_끝나지_않은_대국으로는_재대결을_만들_수_없다(self):
            env = Env()
            game = env.games.start_game(GameMode.INVITE, HOST, GUEST)

            with pytest.raises(InvalidInput):
                env.games.start_rematch(game)

        def test_실패_한_사람이_이미_다른_대국_중이면_ALREADY_IN_GAME(self):
            env = Env()
            previous = env.games.get_game(env.finished_game(), "host")
            env.games.start_game(GameMode.INVITE, HOST, GamePlayer("other", "남", SkinPreference(18, 19)))

            with pytest.raises(AlreadyInGame):
                env.games.start_rematch(previous)


class TestRematchService:
    class TestRequest:
        def test_성공_요청하면_상대에게_알리고_30초_마감을_예약한다(self):
            env = Env()
            game_id = env.finished_game()

            env.rematches.request_rematch(game_id, "host")

            assert env.notifier.requested == [(game_id, "guest")]
            assert env.timer.scheduled[-1][2] == REMATCH_WINDOW_MS

        def test_성공_상대가_수락하면_새_대국이_두_사람에게_시작된다(self):
            env = Env()
            game_id = env.finished_game()
            env.rematches.request_rematch(game_id, "host")

            env.rematches.request_rematch(game_id, "guest")

            new_game = env.publisher.started[-1]
            assert new_game.id != game_id
            assert env.games.find_current_game("host").id == new_game.id

        def test_성공_봇_대국은_요청하자마자_새_대국이_시작된다(self):
            env = Env()
            bot = GamePlayer("bot:EASY", "컴퓨터", SkinPreference(17, 16), is_bot=True)
            game = env.games.start_game(GameMode.BOT, HOST, bot, bot_difficulty="EASY")
            env.games.forfeit(game.id, "host")

            env.rematches.request_rematch(game.id, "host")

            assert env.publisher.started[-1].mode is GameMode.BOT
            assert env.publisher.started[-1].bot_difficulty == "EASY"
            assert env.notifier.requested == []

        def test_실패_진행_중인_대국이면_재대결을_요청할_수_없다(self):
            env = Env()
            game = env.games.start_game(GameMode.INVITE, HOST, GUEST)

            with pytest.raises(InvalidInput):
                env.rematches.request_rematch(game.id, "host")

        def test_실패_새_대국을_만들_수_없으면_두_사람에게_취소를_알린다(self):
            env = Env()
            game_id = env.finished_game()
            env.rematches.request_rematch(game_id, "host")
            env.games.start_game(GameMode.INVITE, GUEST, GamePlayer("other", "남", SkinPreference(18, 19)))

            env.rematches.request_rematch(game_id, "guest")

            assert sorted(env.notifier.cancelled) == [(game_id, "guest", "UNAVAILABLE"), (game_id, "host", "UNAVAILABLE")]

    class TestDeclineAndLeave:
        def test_성공_거절하면_요청한_사람에게_알리고_이후_요청은_거부한다(self):
            env = Env()
            game_id = env.finished_game()
            env.rematches.request_rematch(game_id, "host")

            env.rematches.decline_rematch(game_id, "guest")

            assert env.notifier.cancelled == [(game_id, "host", "DECLINED")]
            with pytest.raises(RematchExpired):
                env.rematches.request_rematch(game_id, "guest")

        def test_성공_결과_화면을_떠나면_상대에게_알린다(self):
            env = Env()
            game_id = env.finished_game()

            env.rematches.leave_result(game_id, "guest")

            assert env.notifier.cancelled == [(game_id, "host", "LEFT")]
            with pytest.raises(RematchExpired):
                env.rematches.request_rematch(game_id, "host")

    class TestExpiry:
        def test_성공_30초가_지나면_두_사람에게_만료를_알린다(self):
            env = Env()
            game_id = env.finished_game()
            env.rematches.request_rematch(game_id, "host")
            env.clock.advance(REMATCH_WINDOW_MS)

            env.timer.fire_latest()

            assert sorted(env.notifier.cancelled) == [(game_id, "guest", "EXPIRED"), (game_id, "host", "EXPIRED")]
