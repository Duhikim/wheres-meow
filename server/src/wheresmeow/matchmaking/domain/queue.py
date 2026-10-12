"""랜덤 매칭 규칙(스펙 4.3). 대기열은 하나이고, 레이팅이 비슷한 사람끼리 먼저 짝짓는다."""

from dataclasses import dataclass

INITIAL_WINDOW = 100
WIDEN_EVERY_MS = 5_000
WIDEN_BY = 50
UNLIMITED_AFTER_MS = 30_000


@dataclass(frozen=True)
class Ticket:
    player_id: str
    rating: int
    joined_at_ms: int


@dataclass(frozen=True)
class Pair:
    first: Ticket  # 먼저 들어온 사람 = 스킨 우선권자
    second: Ticket


def rating_window(ticket: Ticket, now_ms: int) -> int | None:
    """받아들일 레이팅 차이. None 이면 제한 없음(30초 이상 기다림)."""
    waited = max(0, now_ms - ticket.joined_at_ms)
    if waited >= UNLIMITED_AFTER_MS:
        return None
    return INITIAL_WINDOW + WIDEN_BY * (waited // WIDEN_EVERY_MS)


def _accepts(ticket: Ticket, diff: int, now_ms: int) -> bool:
    window = rating_window(ticket, now_ms)
    return window is None or diff <= window


def find_pairs(tickets: list[Ticket], now_ms: int) -> list[Pair]:
    """먼저 들어온 순서로, 서로의 범위 안에서 레이팅이 가장 가까운 상대와 짝짓는다. 한 사람은 한 번만 배정한다."""
    waiting = sorted(tickets, key=lambda t: t.joined_at_ms)
    paired: set[str] = set()
    pairs: list[Pair] = []
    for ticket in waiting:
        if ticket.player_id in paired:
            continue
        candidates = [
            other
            for other in waiting
            if other.player_id != ticket.player_id
            and other.player_id not in paired
            and _accepts(ticket, abs(ticket.rating - other.rating), now_ms)
            and _accepts(other, abs(ticket.rating - other.rating), now_ms)
        ]
        if not candidates:
            continue
        partner = min(candidates, key=lambda o: (abs(ticket.rating - o.rating), o.joined_at_ms))
        first, second = sorted((ticket, partner), key=lambda t: t.joined_at_ms)
        pairs.append(Pair(first, second))
        paired.update({ticket.player_id, partner.player_id})
    return pairs
