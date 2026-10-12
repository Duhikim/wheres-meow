"""12x12 판과 고양이(지뢰) 배치."""

import random
from collections.abc import Iterator
from typing import Protocol

BOARD_SIZE = 12
CAT_COUNT = 25

Position = tuple[int, int]  # (x, y)


class MineLayoutGenerator(Protocol):
    def generate(self, size: int, cat_count: int) -> frozenset[Position]: ...


class RandomMineLayoutGenerator:
    """운영용. 기본값은 OS 난수(secrets 와 같은 출처)를 쓴다."""

    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng or random.SystemRandom()

    def generate(self, size: int, cat_count: int) -> frozenset[Position]:
        cells = [(x, y) for y in range(size) for x in range(size)]
        return frozenset(self._rng.sample(cells, cat_count))


class SeededMineLayoutGenerator(RandomMineLayoutGenerator):
    """테스트·E2E 용. 같은 시드면 항상 같은 배치를 만든다."""

    def __init__(self, seed: int) -> None:
        super().__init__(random.Random(seed))


class FixedMineLayoutGenerator:
    """테스트용. 미리 정한 배치를 그대로 돌려준다."""

    def __init__(self, cats: set[Position]) -> None:
        self._cats = frozenset(cats)

    def generate(self, size: int, cat_count: int) -> frozenset[Position]:
        return self._cats


class Board:
    def __init__(self, size: int, cats: frozenset[Position]) -> None:
        if size <= 0:
            raise ValueError(f"판 크기는 양수여야 합니다: {size}")
        if not cats or len(cats) >= size * size:
            raise ValueError(f"고양이 수가 올바르지 않습니다: {len(cats)}")
        outside = [p for p in cats if not (0 <= p[0] < size and 0 <= p[1] < size)]
        if outside:
            raise ValueError(f"판 밖의 고양이 위치가 있습니다: {outside}")
        self.size = size
        self.cats = cats
        self._counts = {
            (x, y): sum(1 for n in self.neighbors(x, y) if n in cats)
            for y in range(size)
            for x in range(size)
        }

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.size and 0 <= y < self.size

    def is_cat(self, x: int, y: int) -> bool:
        return (x, y) in self.cats

    def adjacent_count(self, x: int, y: int) -> int:
        return self._counts[(x, y)]

    def neighbors(self, x: int, y: int) -> Iterator[Position]:
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if (dx or dy) and self.in_bounds(x + dx, y + dy):
                    yield (x + dx, y + dy)
