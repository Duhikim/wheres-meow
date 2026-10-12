"""컴퓨터 대전의 판단. 사람에게 보이는 정보(열린 숫자, 찾은 고양이, 남은 수)만 입력으로 받는다.

정답 배치는 절대 받지 않는다. 이 모듈은 game 도메인을 모른다(어댑터가 BoardView 로 바꿔 넘긴다).
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from enum import StrEnum
from math import comb
from typing import Protocol

Position = tuple[int, int]

MAX_COMPONENT_CELLS = 24  # 이보다 큰 경계 구간은 배치를 세지 않고 근사한다(스펙 4.6)
MAX_SEARCH_STEPS = 200_000  # 세는 도중 이 단계를 넘으면 근사로 바꾼다. gevent 루프를 오래 막지 않기 위함
EASY_CERTAIN_RATE = 0.3


class Difficulty(StrEnum):
    EASY = "EASY"
    NORMAL = "NORMAL"
    HARD = "HARD"


class Random(Protocol):
    def random(self) -> float: ...

    def choice[T](self, seq: Sequence[T]) -> T: ...


@dataclass(frozen=True)
class BoardView:
    size: int
    numbers: dict[Position, int]  # 열린 숫자·빈 칸과 그 주변 고양이 수
    found: frozenset[Position]  # 이미 찾은 고양이
    remaining: int  # 아직 못 찾은 고양이 수

    def neighbors(self, x: int, y: int) -> Iterable[Position]:
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                nx, ny = x + dx, y + dy
                if (dx or dy) and 0 <= nx < self.size and 0 <= ny < self.size:
                    yield nx, ny

    def closed_cells(self) -> set[Position]:
        return {
            (x, y)
            for y in range(self.size)
            for x in range(self.size)
            if (x, y) not in self.numbers and (x, y) not in self.found
        }


@dataclass(frozen=True)
class _Constraint:
    cells: frozenset[Position]  # 이 숫자 주변의 닫힌 칸
    need: int  # 그 안에 있어야 하는 고양이 수


def _constraints(view: BoardView) -> list[_Constraint]:
    closed = view.closed_cells()
    result = []
    for (x, y), number in view.numbers.items():
        around = list(view.neighbors(x, y))
        cells = frozenset(n for n in around if n in closed)
        if cells:
            need = number - sum(1 for n in around if n in view.found)
            result.append(_Constraint(cells, need))
    return result


def certain_cats(view: BoardView) -> set[Position]:
    """숫자 하나만 보고 확정되는 고양이(남은 수 = 닫힌 이웃 수)."""
    return {cell for c in _constraints(view) if c.need > 0 and c.need == len(c.cells) for cell in c.cells}


def choose_cell(view: BoardView, difficulty: Difficulty, rng: Random) -> Position:
    closed = view.closed_cells()
    if not closed:
        raise ValueError("열 수 있는 칸이 없습니다")
    if difficulty is Difficulty.HARD:
        return _most_likely(view, closed, rng)
    sure = certain_cats(view)
    if sure and (difficulty is Difficulty.NORMAL or rng.random() < EASY_CERTAIN_RATE):
        return rng.choice(sorted(sure))
    if difficulty is Difficulty.NORMAL:
        # 보통은 무작위로 두되, 숫자로 안전이 확정된 칸(명백히 손해인 수)은 피한다
        candidates = closed - certain_safe(view)
        return rng.choice(sorted(candidates or closed))
    return rng.choice(sorted(closed))


def certain_safe(view: BoardView) -> set[Position]:
    """숫자 하나만 보고 확정되는 안전한 칸(남은 고양이가 0 인 숫자 옆의 닫힌 칸)."""
    return {cell for c in _constraints(view) if c.need == 0 for cell in c.cells}


# ---- 어려움: 확률 계산 ----


def _components(constraints: list[_Constraint]) -> list[list[_Constraint]]:
    """칸을 공유하는 숫자끼리 묶는다. 서로 다른 묶음은 독립으로 계산한다."""
    groups: list[tuple[set[Position], list[_Constraint]]] = []
    for constraint in constraints:
        merged_cells, merged = set(constraint.cells), [constraint]
        rest = []
        for cells, members in groups:
            if cells & merged_cells:
                merged_cells |= cells
                merged += members
            else:
                rest.append((cells, members))
        groups = [*rest, (merged_cells, merged)]
    return [members for _, members in groups]


class _TooManySteps(Exception):
    pass


def _enumerate(constraints: list[_Constraint], unconstrained: int, remaining: int) -> dict[Position, float] | None:
    """가능한 배치를 모두 세어 칸별 고양이 확률을 낸다. 배치가 없거나 너무 많으면 None."""
    cells = sorted({cell for c in constraints for cell in c.cells})
    index = {cell: i for i, cell in enumerate(cells)}
    members = [[index[cell] for cell in c.cells] for c in constraints]
    by_cell = [[ci for ci, m in enumerate(members) if i in m] for i in range(len(cells))]
    count = [0] * len(constraints)  # 지금까지 고양이로 둔 수
    left = [len(m) for m in members]  # 아직 정하지 않은 칸 수
    assignment = [False] * len(cells)
    totals = [0.0] * len(cells)
    weight_sum = 0.0
    steps = 0

    def place(i: int, cats: int) -> None:
        nonlocal weight_sum, steps
        steps += 1
        if steps > MAX_SEARCH_STEPS:
            raise _TooManySteps
        if i == len(cells):
            if any(count[ci] != c.need for ci, c in enumerate(constraints)):
                return
            outside = remaining - cats
            if outside < 0 or outside > unconstrained:
                return
            weight = comb(unconstrained, outside)  # 나머지 칸에 남은 고양이를 놓는 경우의 수
            weight_sum += weight
            for k, is_cat in enumerate(assignment):
                if is_cat:
                    totals[k] += weight
            return
        for is_cat in (False, True):
            ok = True
            for ci in by_cell[i]:
                left[ci] -= 1
                count[ci] += is_cat
                if count[ci] > constraints[ci].need or count[ci] + left[ci] < constraints[ci].need:
                    ok = False
            if ok:
                assignment[i] = is_cat
                place(i + 1, cats + is_cat)
            for ci in by_cell[i]:
                left[ci] += 1
                count[ci] -= is_cat

    try:
        place(0, 0)
    except _TooManySteps:
        return None
    if weight_sum == 0:
        return None  # 모순된 판
    return {cell: totals[i] / weight_sum for i, cell in enumerate(cells)}


def _approximate(constraints: list[_Constraint]) -> dict[Position, float]:
    """근사: 각 칸이 속한 숫자들 중 (남은 고양이 / 닫힌 칸) 이 가장 큰 값."""
    probabilities: dict[Position, float] = {}
    for c in constraints:
        p = min(1.0, max(0.0, c.need / len(c.cells)))
        for cell in c.cells:
            probabilities[cell] = max(probabilities.get(cell, 0.0), p)
    return probabilities


def _most_likely(view: BoardView, closed: set[Position], rng: Random) -> Position:
    constraints = _constraints(view)
    frontier = {cell for c in constraints for cell in c.cells}
    unconstrained = len(closed - frontier)
    probabilities: dict[Position, float] = {}
    for component in _components(constraints):
        size = len({cell for c in component for cell in c.cells})
        exact = _enumerate(component, unconstrained, view.remaining) if size <= MAX_COMPONENT_CELLS else None
        probabilities.update(exact if exact is not None else _approximate(component))
    if unconstrained:
        expected_frontier = sum(probabilities.values())
        outside = min(1.0, max(0.0, (view.remaining - expected_frontier) / unconstrained))
        for cell in closed - frontier:
            probabilities[cell] = outside
    best = max(probabilities.values())
    return rng.choice(sorted(cell for cell, p in probabilities.items() if p >= best - 1e-9))
