import pytest

from fakes import FakeClock, FakeGameEventPublisher, FakeGameResultRecorder, FakeTurnTimer
from wheresmeow.bot.adapter.inbound.game_events.bot_turn_driver import BotTurnDriver, to_view
from wheresmeow.game.adapter.outbound.memory.in_memory_game_store import InMemoryGameStore
from wheresmeow.game.adapter.outbound.composite_publisher import CompositeGameEventPublisher
from wheresmeow.game.application.port.inbound import GamePlayer
from wheresmeow.game.application.service.game_service import GameService
from wheresmeow.game.domain.board import Board, FixedMineLayoutGenerator
from wheresmeow.game.domain.game import CellsRevealed, Game, GameMode, Seat
from wheresmeow.game.domain.skins import SkinPreference

CATS = {(x, y) for y in range(10, 12) for x in range(12)} | {(11, 9)}
HUMAN = GamePlayer("human", "사람냥", SkinPreference(16, 17))
BOT = GamePlayer("bot:NORMAL", "컴퓨터 (보통)", SkinPreference(17, 16), is_bot=True)


class QueueScheduler:
    """예약만 쌓아 두고, run_all() 로 직접 실행한다."""

    def __init__(self) -> None:
        self.queue = []

    def __call__(self, task) -> None:
        self.queue.append(task)

    def run_all(self) -> None:
        while self.queue:
            self.queue.pop(0)()


def make_env(first_seat: int):
    scheduler = QueueScheduler()
    driver = BotTurnDriver(scheduler)
    fake = FakeGameEventPublisher()
    service = GameService(
        InMemoryGameStore(),
        CompositeGameEventPublisher([fake, driver]),
        FakeTurnTimer(),
        FixedMineLayoutGenerator(CATS),
        FakeClock(0),
        recorder=FakeGameResultRecorder(),
        first_seat_chooser=lambda: first_seat,
        id_factory=lambda: "g1",
    )
    driver.attach(get_game=service, reveal=service)
    return service, driver, scheduler, fake


class TestToView:
    class TestMapping:
        def test_성공_보이는_정보만_넘기고_고양이_위치는_넘기지_않는다(self):
            seats = (Seat("a", "a", 16), Seat("b", "b", 17))
            game = Game("g", GameMode.BOT, Board(4, frozenset({(0, 0), (3, 3)})), seats, 0, 0, bot_difficulty="EASY")
            game.reveal("a", 0, 0, now_ms=0)  # 고양이
            game.reveal("a", 1, 0, now_ms=0)  # 숫자 1

            view = to_view(game)

            assert view.numbers == {(1, 0): 1}
            assert view.found == frozenset({(0, 0)})
            assert view.remaining == 1
            assert (3, 3) not in view.numbers and (3, 3) not in view.found


class TestBotTurnDriver:
    class TestMove:
        def test_성공_봇이_선공이면_시작하자마자_수를_예약하고_둔다(self):
            service, _, scheduler, fake = make_env(first_seat=1)
            service.start_game(GameMode.BOT, HUMAN, BOT, bot_difficulty="NORMAL")

            assert len(scheduler.queue) == 1
            scheduler.run_all()

            moves = [e for _, events in fake.published for e in events if isinstance(e, CellsRevealed)]
            assert moves and moves[0].seat == 1

        def test_성공_사람_차례에는_아무것도_예약하지_않는다(self):
            service, _, scheduler, _ = make_env(first_seat=0)

            service.start_game(GameMode.BOT, HUMAN, BOT, bot_difficulty="NORMAL")

            assert scheduler.queue == []

        def test_성공_사람이_숫자_칸을_열면_봇_차례가_예약된다(self):
            service, _, scheduler, _ = make_env(first_seat=0)
            service.start_game(GameMode.BOT, HUMAN, BOT, bot_difficulty="NORMAL")

            service.reveal("g1", "human", 5, 9)

            assert len(scheduler.queue) == 1

        def test_성공_생각하는_사이_대국이_끝났으면_두지_않는다(self):
            service, _, scheduler, fake = make_env(first_seat=1)
            service.start_game(GameMode.BOT, HUMAN, BOT, bot_difficulty="NORMAL")
            service.forfeit("g1", "human")
            published = len(fake.published)

            scheduler.run_all()

            assert len(fake.published) == published

        def test_성공_사람끼리의_대국에는_관여하지_않는다(self):
            service, _, scheduler, _ = make_env(first_seat=1)

            service.start_game(GameMode.INVITE, HUMAN, GamePlayer("p2", "둘째", SkinPreference(18, 19)))

            assert scheduler.queue == []

    class TestAttach:
        def test_실패_연결하지_않고_쓰면_오류다(self):
            driver = BotTurnDriver(QueueScheduler())
            seats = (Seat("a", "a", 16), Seat("bot:EASY", "b", 17, is_bot=True))
            game = Game("g", GameMode.BOT, Board(4, frozenset({(0, 0)})), seats, 1, 0, bot_difficulty="EASY")

            with pytest.raises(RuntimeError):
                driver.game_started(game)
