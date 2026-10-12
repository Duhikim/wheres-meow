import pytest

from fakes import FakeClock
from wheresmeow.matchmaking.application.port.outbound import MatchPlayer
from wheresmeow.matchmaking.application.service.matchmaking_service import MatchmakingService
from wheresmeow.matchmaking.domain.errors import AlreadyInGame, AlreadyQueued
from wheresmeow.shared.errors import DomainError

T0 = 1_000_000


class FakeDirectory:
    def profile(self, player_id: str) -> MatchPlayer:
        return MatchPlayer(player_id, f"{player_id}냥", 16, 17)


class FakeRatings:
    def __init__(self, **ratings: int) -> None:
        self.ratings = ratings

    def rating_of(self, player_id: str) -> int:
        return self.ratings.get(player_id, 1000)


class FakeStarter:
    def __init__(self) -> None:
        self.started: list[tuple[str, str]] = []
        self.in_game: set[str] = set()
        self.fail_with: Exception | None = None

    def is_in_game(self, player_id: str) -> bool:
        return player_id in self.in_game

    def start_match(self, first: MatchPlayer, second: MatchPlayer) -> None:
        if self.fail_with:
            raise self.fail_with
        self.started.append((first.player_id, second.player_id))
        self.in_game.update({first.player_id, second.player_id})


class FakeNotifier:
    def __init__(self) -> None:
        self.waiting: list[tuple[str, int, int | None]] = []

    def waiting_started(self, player_id: str, since_ms: int, rating_range: int | None) -> None:
        self.waiting.append((player_id, since_ms, rating_range))


class Env:
    def __init__(self, **ratings: int) -> None:
        self.clock = FakeClock(now_ms=T0)
        self.starter = FakeStarter()
        self.notifier = FakeNotifier()
        self.service = MatchmakingService(
            FakeDirectory(), FakeRatings(**ratings), self.starter, self.notifier, self.clock
        )


class TestMatchmakingService:
    class TestJoin:
        def test_성공_대기열에_넣고_대기_시작을_알린다(self):
            env = Env()

            env.service.join_match("a")

            assert env.service.is_queued("a")
            assert env.notifier.waiting == [("a", T0, 100)]

        def test_실패_이미_대기_중이면_ALREADY_QUEUED(self):
            env = Env()
            env.service.join_match("a")

            with pytest.raises(AlreadyQueued):
                env.service.join_match("a")

        def test_실패_진행_중인_대국이_있으면_ALREADY_IN_GAME(self):
            env = Env()
            env.starter.in_game.add("a")

            with pytest.raises(AlreadyInGame):
                env.service.join_match("a")
            assert not env.service.is_queued("a")

    class TestLeave:
        def test_성공_대기열에서_빠진다(self):
            env = Env()
            env.service.join_match("a")

            env.service.leave_match("a")

            assert not env.service.is_queued("a")

        def test_성공_대기_중이_아니어도_조용히_넘어간다_연결_끊김(self):
            Env().service.leave_match("nobody")

    class TestTick:
        def test_성공_범위_안의_두_사람을_짝지어_먼저_온_사람을_우선권자로_대국을_시작한다(self):
            env = Env(a=1000, b=1050)
            env.service.join_match("a")
            env.clock.advance(1_000)
            env.service.join_match("b")

            env.service.tick()

            assert env.starter.started == [("a", "b")]
            assert not env.service.is_queued("a") and not env.service.is_queued("b")

        def test_성공_범위_밖이면_기다리고_시간이_지나면_짝짓는다(self):
            env = Env(a=1000, b=1300)
            env.service.join_match("a")
            env.service.join_match("b")

            env.service.tick()
            assert env.starter.started == []

            env.clock.advance(30_000)
            env.service.tick()
            assert env.starter.started == [("a", "b")]

        def test_성공_대국_시작에_실패하면_대국에_들어가지_않은_사람은_원래_순서대로_다시_기다린다(self):
            env = Env()
            env.service.join_match("a")
            env.service.join_match("b")
            env.starter.in_game.add("b")  # 그 사이 b 가 컴퓨터 대전을 시작했다
            env.starter.fail_with = DomainError("이미 대국 중")

            env.service.tick()

            assert env.service.is_queued("a") and not env.service.is_queued("b")
            assert env.service.waiting_since("a") == T0

        def test_성공_예상하지_못한_예외도_로그를_남기고_다음_틱은_계속된다(self, caplog):
            env = Env()
            env.service.join_match("a")
            env.service.join_match("b")
            env.starter.fail_with = RuntimeError("boom")

            env.service.tick()

            assert "매칭 대국 시작 실패" in caplog.text
            env.starter.fail_with = None
            env.service.tick()
            assert env.starter.started == [("a", "b")]
