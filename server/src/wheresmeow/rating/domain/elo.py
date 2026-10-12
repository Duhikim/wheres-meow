"""Elo 레이팅(스펙 4.5). 초기 1000, K=32. 승리 1, 무승부 0.5, 패배·기권·자동 기권 0."""

from enum import StrEnum

INITIAL_RATING = 1000
K_FACTOR = 32


class Outcome(StrEnum):
    FIRST_WINS = "FIRST_WINS"
    SECOND_WINS = "SECOND_WINS"
    DRAW = "DRAW"


def expected_score(rating: int, opponent: int) -> float:
    return 1 / (1 + 10 ** ((opponent - rating) / 400))


def rate(first: int, second: int, outcome: Outcome) -> tuple[int, int]:
    """새 레이팅 (첫째, 둘째). 한쪽 변화량을 반올림하고 다른 쪽은 그 반대로 두어 합이 항상 0 이다."""
    score = {Outcome.FIRST_WINS: 1.0, Outcome.SECOND_WINS: 0.0, Outcome.DRAW: 0.5}[outcome]
    delta = round(K_FACTOR * (score - expected_score(first, second)))
    return first + delta, second - delta
