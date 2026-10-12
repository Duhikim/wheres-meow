"""rating 도메인이 바깥에 제공하는 조회 유스케이스(스펙 4.5 랭킹·프로필)."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class RatingSummary:
    rating: int
    games: int
    wins: int
    losses: int
    draws: int


@dataclass(frozen=True)
class RankingEntry:
    rank: int
    player_id: str
    nickname: str
    skin: int
    summary: RatingSummary


@dataclass(frozen=True)
class RankingPage:
    page: int
    total_pages: int
    entries: list[RankingEntry]


@dataclass(frozen=True)
class RecentGame:
    game_id: str
    mode: str
    ended_at_ms: int
    opponent_id: str
    opponent_nickname: str
    my_score: int
    opponent_score: int
    result: str  # WIN·LOSS·DRAW
    rating_before: int | None  # 결과를 저장하지 못했던 대국이면 None
    rating_after: int | None


@dataclass(frozen=True)
class Profile:
    player_id: str
    nickname: str
    kind: str
    skin: int
    rating: RatingSummary
    ranked: bool  # 랭킹에 나오는 조건(회원, 5판 이상)을 채웠는지
    recent_games: list[RecentGame]
    bot_records: list[dict]


class GetRankingsUseCase(Protocol):
    def rankings(self, page: int) -> RankingPage: ...


class GetProfileUseCase(Protocol):
    def profile(self, player_id: str) -> Profile: ...
