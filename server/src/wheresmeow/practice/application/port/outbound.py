"""practice 도메인이 바깥에 요구하는 기능."""

from dataclasses import dataclass
from typing import Protocol

from wheresmeow.practice.domain.record import Difficulty


@dataclass(frozen=True)
class SingleRecord:
    best_ms: int
    clears: int


class SingleRecordStore(Protocol):
    def records_of(self, player_id: str) -> dict[Difficulty, SingleRecord]: ...

    def record_clear(
        self, player_id: str, difficulty: Difficulty, elapsed_ms: int, now_ms: int
    ) -> tuple[SingleRecord, bool]:
        """클리어 한 번을 원자적으로 반영한다. (갱신 뒤 기록, 최고 기록을 새로 세웠는지)."""
        ...
