"""practice 도메인이 바깥에 제공하는 유스케이스."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ClearResult:
    difficulty: str
    best_ms: int
    new_best: bool
    clears: int


class SubmitClearUseCase(Protocol):
    def submit_clear(self, player_id: str, difficulty: str, elapsed_ms: int) -> ClearResult: ...


class SingleRecordsUseCase(Protocol):
    def records(self, player_id: str) -> list[dict]:
        """세 난이도 모두, 기록이 없으면 bestMs 가 None."""
        ...
