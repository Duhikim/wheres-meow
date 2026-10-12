import threading

import pytest

from fakes import FakeClock, FakeGameEventPublisher, FakeGameResultRecorder, FakeTurnTimer
from wheresmeow.game.adapter.outbound.memory.in_memory_game_store import InMemoryGameStore
from wheresmeow.game.application.port.inbound import GamePlayer
from wheresmeow.game.application.service.game_service import GameService
from wheresmeow.game.domain.board import FixedMineLayoutGenerator
from wheresmeow.game.domain.errors import AlreadyInGame, GameNotFound, NotAParticipant
from wheresmeow.game.domain.game import TURN_MS, CellsRevealed, GameEnded, GameMode, TurnTimedOut
from wheresmeow.game.domain.skins import SkinPreference

# 12x12 판. 고양이를 아래쪽 두 줄과 (11,9) 에 몰아 두어 (0,0) 은 빈 칸이다.
CATS = {(x, y) for y in range(10, 12) for x in range(0, 12)} | {(11, 9)}  # 24 + 1 = 25
HOST = GamePlayer("host", "방장", SkinPreference(16, 17))
GUEST = GamePlayer("guest", "손님", SkinPreference(16, 20))


@pytest.fixture
def env():
    clock = FakeClock(now_ms=0)
    store = InMemoryGameStore()
    publisher = FakeGameEventPublisher()
    timer = FakeTurnTimer()
    recorder = FakeGameResultRecorder()
    service = GameService(
        store,
        publisher,
        timer,
        FixedMineLayoutGenerator(CATS),
        clock,
        recorder=recorder,
        first_seat_chooser=lambda: 0,
        id_factory=lambda: "g1",
    )
    service.recorder = recorder  # 테스트에서 꺼내 쓰기 위한 참조
    return service, store, publisher, timer, clock


class TestGameService:
    class TestStartGame:
        def test_성공_대국을_만들고_시작을_알리고_첫_턴_타이머를_예약한다(self, env):
            service, store, publisher, timer, _ = env

            game = service.start_game(GameMode.INVITE, HOST, GUEST)

            assert store.get("g1") is game
            assert publisher.started == [game]
            assert [(gid, seq, deadline) for gid, seq, deadline, _ in timer.scheduled] == [("g1", 1, TURN_MS)]

        def test_성공_우선권자가_좌석_0이고_1P가_겹치면_상대가_2P를_쓴다(self, env):
            service, *_ = env

            game = service.start_game(GameMode.INVITE, HOST, GUEST)

            assert game.seats[0].player_id == "host"
            assert (game.seats[0].skin, game.seats[1].skin) == (16, 20)

        def test_실패_진행_중인_대국이_있으면_거부한다(self, env):
            service, *_ = env
            service.start_game(GameMode.INVITE, HOST, GUEST)

            with pytest.raises(AlreadyInGame):
                service.start_game(GameMode.INVITE, HOST, GamePlayer("other", "다른", SkinPreference()))

    class TestReveal:
        def test_성공_이벤트를_발행하고_다음_턴_타이머를_예약한다(self, env):
            service, _, publisher, timer, clock = env
            service.start_game(GameMode.INVITE, HOST, GUEST)
            clock.advance(3000)

            service.reveal("g1", "host", 0, 0)

            [(game_id, [event])] = publisher.published
            assert game_id == "g1"
            assert isinstance(event, CellsRevealed)
            assert timer.scheduled[-1][:3] == ("g1", 2, 3000 + TURN_MS)

        def test_성공_대국이_끝나면_타이머를_예약하지_않고_새_대국을_시작할_수_있다(self, env):
            service, _, publisher, timer, _ = env
            service.start_game(GameMode.INVITE, HOST, GUEST)
            scheduled_before = len(timer.scheduled)

            service.forfeit("g1", "guest")

            assert isinstance(publisher.published[-1][1][-1], GameEnded)
            assert len(timer.scheduled) == scheduled_before
            service.start_game(GameMode.INVITE, HOST, GUEST)  # 예외 없음

        def test_실패_없는_대국이면_거부한다(self, env):
            service, *_ = env

            with pytest.raises(GameNotFound):
                service.reveal("nope", "host", 0, 0)

        def test_성공_같은_칸을_동시에_두_번_눌러도_한_번만_적용된다(self, env):
            service, _, publisher, _, _ = env
            service.start_game(GameMode.INVITE, HOST, GUEST)
            errors: list[Exception] = []

            def tap():
                try:
                    service.reveal("g1", "host", 11, 9)  # 고양이 칸
                except Exception as error:  # noqa: BLE001 - 두 번째 요청의 예외를 모은다
                    errors.append(error)

            threads = [threading.Thread(target=tap) for _ in range(2)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

            assert len(publisher.published) == 1
            assert [type(e).__name__ for e in errors] == ["CellAlreadyOpen"]

    class TestHandleTimeout:
        def test_성공_만료되면_감점_이벤트를_발행한다(self, env):
            service, _, publisher, timer, _ = env
            service.start_game(GameMode.INVITE, HOST, GUEST)

            timer.fire_latest()

            [(_, [event])] = publisher.published
            assert isinstance(event, TurnTimedOut)
            assert event.scores == (-1, 0)

        def test_성공_지나간_턴의_만료는_아무것도_발행하지_않는다(self, env):
            service, _, publisher, timer, _ = env
            service.start_game(GameMode.INVITE, HOST, GUEST)
            first_turn = timer.scheduled[0]
            service.reveal("g1", "host", 0, 0)
            published_before = len(publisher.published)

            first_turn[3]("g1", first_turn[1])

            assert len(publisher.published) == published_before

        def test_성공_기권으로_끝난_뒤_이전_턴의_만료는_아무것도_발행하지_않는다(self, env):
            service, _, publisher, timer, _ = env
            service.start_game(GameMode.INVITE, HOST, GUEST)
            service.forfeit("g1", "guest")
            published_before = len(publisher.published)

            timer.fire_latest()  # 시작 시 예약된 첫 턴 타이머

            assert len(publisher.published) == published_before

        def test_성공_없는_대국의_만료는_무시한다(self, env):
            service, *_ = env

            service.handle_timeout("nope", 1)  # 예외 없음

    class TestGetGame:
        def test_성공_참가자는_대국을_조회한다(self, env):
            service, *_ = env
            service.start_game(GameMode.INVITE, HOST, GUEST)

            assert service.get_game("g1", "guest").id == "g1"

        def test_실패_참가자가_아니면_거부한다(self, env):
            service, *_ = env
            service.start_game(GameMode.INVITE, HOST, GUEST)

            with pytest.raises(NotAParticipant):
                service.get_game("g1", "stranger")


class TestGameServiceRecording:
    class TestRecord:
        def test_성공_대국이_끝나면_결과를_한_번_기록한다(self, env):
            service, *_ = env
            service.start_game(GameMode.INVITE, HOST, GUEST)
            service.reveal("g1", "host", 0, 0)

            service.forfeit("g1", "guest")

            assert service.recorder.recorded == ["g1"]

        def test_성공_진행_중에는_기록하지_않는다(self, env):
            service, *_ = env
            service.start_game(GameMode.INVITE, HOST, GUEST)

            service.reveal("g1", "host", 0, 0)

            assert service.recorder.recorded == []

        def test_성공_기록이_실패해도_종료_알림은_보내고_로그를_남긴다(self, env, caplog):
            service, _, publisher, _, _ = env
            service.start_game(GameMode.INVITE, HOST, GUEST)
            service.recorder.fail_with = RuntimeError("db down")

            service.forfeit("g1", "guest")

            assert isinstance(publisher.published[-1][1][-1], GameEnded)
            assert "대국 결과 저장 실패" in caplog.text
            assert "g1" in caplog.text


class TestGameServiceCurrentGame:
    class TestFindCurrentGame:
        def test_성공_진행_중인_대국을_찾는다(self, env):
            service, *_ = env
            service.start_game(GameMode.INVITE, HOST, GUEST)

            assert service.find_current_game("guest").id == "g1"

        def test_성공_끝난_대국은_찾지_않는다(self, env):
            service, *_ = env
            service.start_game(GameMode.INVITE, HOST, GUEST)
            service.forfeit("g1", "host")

            assert service.find_current_game("host") is None
