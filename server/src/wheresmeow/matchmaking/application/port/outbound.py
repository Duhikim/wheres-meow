"""matchmaking 도메인이 바깥에 요구하는 기능."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class MatchPlayer:
    player_id: str
    nickname: str
    skin_1p: int
    skin_2p: int


class PlayerDirectory(Protocol):
    def profile(self, player_id: str) -> MatchPlayer: ...


class RatingLookup(Protocol):
    def rating_of(self, player_id: str) -> int:
        """사람 간 대국을 아직 마치지 않았으면 초기 레이팅."""
        ...


class MatchGameStarter(Protocol):
    def is_in_game(self, player_id: str) -> bool: ...

    def start_match(self, first: MatchPlayer, second: MatchPlayer) -> None:
        """first 가 스킨 우선권자다(대기열 선착순, 스펙 4.3)."""
        ...


class MatchNotifier(Protocol):
    def waiting_started(self, player_id: str, since_ms: int, rating_range: int | None) -> None:
        """match:waiting. rating_range 가 None 이면 범위 제한 없음."""
        ...
