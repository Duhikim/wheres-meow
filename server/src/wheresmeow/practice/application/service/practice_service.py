from wheresmeow.practice.application.port.inbound import ClearResult
from wheresmeow.practice.application.port.outbound import SingleRecordStore
from wheresmeow.practice.domain.record import Difficulty, parse_difficulty, validate_elapsed
from wheresmeow.shared.clock import Clock


class PracticeService:
    """SubmitClear·SingleRecords 유스케이스 구현. 전적은 세지 않고 난이도별 최고 기록과 클리어 횟수만 남긴다."""

    def __init__(self, store: SingleRecordStore, clock: Clock) -> None:
        self._store = store
        self._clock = clock

    def submit_clear(self, player_id: str, difficulty: str, elapsed_ms: int) -> ClearResult:
        level = parse_difficulty(difficulty)
        record, new_best = self._store.record_clear(player_id, level, validate_elapsed(elapsed_ms), self._clock.now_ms())
        return ClearResult(level.value, record.best_ms, new_best, record.clears)

    def records(self, player_id: str) -> list[dict]:
        records = self._store.records_of(player_id)
        result = []
        for level in Difficulty:
            record = records.get(level)
            result.append({
                "difficulty": level.value,
                "bestMs": record.best_ms if record else None,
                "clears": record.clears if record else 0,
            })
        return result
