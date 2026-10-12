import pytest

from wheresmeow.game.domain.board import (
    BOARD_SIZE,
    CAT_COUNT,
    Board,
    RandomMineLayoutGenerator,
    SeededMineLayoutGenerator,
)


class TestBoard:
    class TestInit:
        def test_실패_판_밖의_고양이가_있으면_거부한다(self):
            with pytest.raises(ValueError):
                Board(3, frozenset({(3, 0)}))

        def test_실패_고양이가_없으면_거부한다(self):
            with pytest.raises(ValueError):
                Board(3, frozenset())

        def test_실패_모든_칸이_고양이면_거부한다(self):
            cats = frozenset((x, y) for x in range(2) for y in range(2))
            with pytest.raises(ValueError):
                Board(2, cats)

    class TestAdjacentCount:
        def test_성공_주변_고양이_수를_센다(self):
            board = Board(3, frozenset({(0, 0), (2, 2)}))

            assert board.adjacent_count(1, 1) == 2
            assert board.adjacent_count(1, 0) == 1
            assert board.adjacent_count(2, 0) == 0

        def test_성공_모서리_칸은_판_밖을_세지_않는다(self):
            board = Board(3, frozenset({(1, 1)}))

            assert board.adjacent_count(0, 0) == 1
            assert len(list(board.neighbors(0, 0))) == 3


class TestRandomMineLayoutGenerator:
    class TestGenerate:
        def test_성공_고양이_25마리를_판_안에_서로_다른_칸에_놓는다(self):
            cats = RandomMineLayoutGenerator().generate(BOARD_SIZE, CAT_COUNT)

            assert len(cats) == CAT_COUNT
            assert all(0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE for x, y in cats)

        def test_성공_같은_시드면_같은_배치를_만든다(self):
            first = SeededMineLayoutGenerator(42).generate(BOARD_SIZE, CAT_COUNT)
            second = SeededMineLayoutGenerator(42).generate(BOARD_SIZE, CAT_COUNT)

            assert first == second
