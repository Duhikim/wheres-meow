import pytest

from fakes import FakeClock
from wheresmeow.practice.application.port.outbound import SingleRecord
from wheresmeow.practice.application.service.practice_service import PracticeService
from wheresmeow.practice.domain.record import MAX_ELAPSED_MS, MIN_ELAPSED_MS, Difficulty
from wheresmeow.shared.errors import InvalidInput


class FakeStore:
    def __init__(self) -> None:
        self.records: dict[tuple[str, Difficulty], SingleRecord] = {}

    def records_of(self, player_id: str) -> dict[Difficulty, SingleRecord]:
        return {d: r for (p, d), r in self.records.items() if p == player_id}

    def record_clear(self, player_id: str, difficulty: Difficulty, elapsed_ms: int, now_ms: int) -> tuple[SingleRecord, bool]:
        previous = self.records.get((player_id, difficulty))
        new_best = previous is None or elapsed_ms < previous.best_ms
        record = SingleRecord(elapsed_ms if new_best else previous.best_ms, (previous.clears if previous else 0) + 1)
        self.records[(player_id, difficulty)] = record
        return record, new_best


def service() -> PracticeService:
    return PracticeService(FakeStore(), FakeClock())


class TestPracticeService:
    class TestSubmitClear:
        def test_성공_첫_클리어는_최고_기록이다(self):
            result = service().submit_clear("p", "BEGINNER", 42_000)

            assert (result.best_ms, result.new_best, result.clears) == (42_000, True, 1)

        def test_성공_더_빠르면_갱신하고_느리면_유지하되_클리어_횟수는_센다(self):
            practice = service()
            practice.submit_clear("p", "BEGINNER", 42_000)

            slower = practice.submit_clear("p", "BEGINNER", 50_000)
            faster = practice.submit_clear("p", "BEGINNER", 30_000)

            assert (slower.best_ms, slower.new_best) == (42_000, False)
            assert (faster.best_ms, faster.new_best, faster.clears) == (30_000, True, 3)

        def test_성공_난이도별로_따로_남긴다(self):
            practice = service()
            practice.submit_clear("p", "BEGINNER", 42_000)

            assert practice.submit_clear("p", "EXPERT", 300_000).new_best is True

        def test_실패_알_수_없는_난이도면_INVALID_INPUT(self):
            with pytest.raises(InvalidInput):
                service().submit_clear("p", "IMPOSSIBLE", 42_000)

        @pytest.mark.parametrize("elapsed", [MIN_ELAPSED_MS - 1, 0, -5, MAX_ELAPSED_MS + 1])
        def test_실패_말이_안_되는_시간이면_INVALID_INPUT(self, elapsed):
            with pytest.raises(InvalidInput):
                service().submit_clear("p", "BEGINNER", elapsed)

    class TestRecords:
        def test_성공_세_난이도를_모두_돌려주고_기록이_없으면_null(self):
            practice = service()
            practice.submit_clear("p", "INTERMEDIATE", 99_000)

            assert practice.records("p") == [
                {"difficulty": "BEGINNER", "bestMs": None, "clears": 0},
                {"difficulty": "INTERMEDIATE", "bestMs": 99_000, "clears": 1},
                {"difficulty": "EXPERT", "bestMs": None, "clears": 0},
            ]
