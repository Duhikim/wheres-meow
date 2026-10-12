"""rating 조회가 바깥에 요구하는 기능."""

from dataclasses import dataclass
from typing import Protocol

from wheresmeow.rating.application.port.inbound import RatingSummary, RecentGame


@dataclass(frozen=True)
class RankedRow:
    player_id: str
    nickname: str
    skin: int
    rating: int
    games: int
    wins: int
    losses: int
    draws: int


@dataclass(frozen=True)
class PlayerCard:
    player_id: str
    nickname: str
    kind: str  # MEMBER·GUEST
    skin: int  # 대표 고양이(1P)


class RatingReader(Protocol):
    def count_ranked(self, min_games: int) -> int:
        """회원이면서 min_games 판 이상 둔 사람 수."""
        ...

    def ranked(self, min_games: int, offset: int, limit: int) -> list[RankedRow]:
        """count_ranked 와 같은 조건으로 레이팅이 높은 순서."""
        ...

    def summary_of(self, player_id: str) -> RatingSummary | None:
        """사람 간 대국을 한 번도 마치지 않았으면 None."""
        ...

    def recent_games(self, player_id: str, limit: int) -> list[RecentGame]:
        """사람 간 대국만, 최근에 끝난 순서."""
        ...


class PlayerDirectory(Protocol):
    def card_of(self, player_id: str) -> PlayerCard:
        """없으면 PLAYER_NOT_FOUND 도메인 예외를 던진다."""
        ...


class BotRecordSource(Protocol):
    def bot_records(self, player_id: str) -> list[dict]: ...
