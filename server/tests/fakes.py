"""여러 도메인의 테스트가 공유하는 가짜 어댑터."""

from collections.abc import Callable, Sequence


class FakeClock:
    def __init__(self, now_ms: int = 1_000_000) -> None:
        self._now = now_ms

    def now_ms(self) -> int:
        return self._now

    def advance(self, ms: int) -> None:
        self._now += ms


class FakeGameEventPublisher:
    def __init__(self) -> None:
        self.started: list = []
        self.published: list = []  # (game_id, events)
        self.rating_changes_at_publish: list = []  # 발행 시점에 대국에 붙어 있던 레이팅 변화

    def game_started(self, game) -> None:
        self.started.append(game)

    def publish(self, game, events: Sequence) -> None:
        self.published.append((game.id, list(events)))
        self.rating_changes_at_publish.append(getattr(game, "rating_changes", None))


class FakeTurnTimer:
    """예약만 기록하고, fire_latest() 를 호출해야 만료가 일어난다."""

    def __init__(self) -> None:
        self.scheduled: list[tuple[str, int, int, Callable[[str, int], None]]] = []

    def schedule(self, game_id: str, turn_seq: int, deadline_ms: int, on_expire) -> None:
        self.scheduled.append((game_id, turn_seq, deadline_ms, on_expire))

    def fire_latest(self) -> None:
        game_id, turn_seq, _, on_expire = self.scheduled[-1]
        on_expire(game_id, turn_seq)


class FakeGameResultRecorder:
    def __init__(self) -> None:
        self.recorded: list = []
        self.fail_with: Exception | None = None
        self.rating_changes = None  # record 가 돌려줄 레이팅 변화

    def record(self, game):
        if self.fail_with:
            raise self.fail_with
        self.recorded.append(game.id)
        return self.rating_changes
