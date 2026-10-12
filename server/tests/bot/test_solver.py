"""봇 판단(solver) 테스트. 판은 손으로 정답을 계산할 수 있게 작게 만든다."""

import random
import time

import pytest

from wheresmeow.bot.domain.solver import BoardView, Difficulty, certain_cats, choose_cell


class FixedRandom:
    """random() 값을 고정하고, choice() 는 첫 원소를 고르는 가짜 난수."""

    def __init__(self, value: float) -> None:
        self.value = value

    def random(self) -> float:
        return self.value

    def choice(self, seq):
        return sorted(seq)[0]


def single_certain_view() -> BoardView:
    # 4x4. (0,0)=1 의 닫힌 이웃은 (1,1) 하나뿐 → (1,1) 은 확실한 고양이
    return BoardView(size=4, numbers={(0, 0): 1, (1, 0): 1, (0, 1): 1}, found=frozenset(), remaining=3)


def one_two_one_view() -> BoardView:
    # 3x3. 아래 줄 1-2-1 → (0,1)·(2,1) 고양이, (1,1) 안전. 숫자 하나로는 아무것도 확정되지 않는다.
    return BoardView(size=3, numbers={(0, 2): 1, (1, 2): 2, (2, 2): 1}, found=frozenset(), remaining=3)


class TestBoardView:
    class TestClosedCells:
        def test_성공_열린_칸과_찾은_고양이를_뺀_칸이_닫힌_칸이다(self):
            view = BoardView(size=2, numbers={(0, 0): 1}, found=frozenset({(1, 1)}), remaining=0)

            assert view.closed_cells() == {(1, 0), (0, 1)}


class TestCertainCats:
    class TestSingleNumber:
        def test_성공_숫자와_닫힌_이웃_수가_같으면_모두_고양이다(self):
            assert certain_cats(single_certain_view()) == {(1, 1)}

        def test_성공_이미_찾은_고양이는_숫자에서_뺀다(self):
            view = BoardView(size=4, numbers={(0, 0): 1}, found=frozenset({(1, 1)}), remaining=2)

            assert certain_cats(view) == set()

        def test_성공_여러_숫자를_엮어야_하는_경우는_찾지_못한다(self):
            assert certain_cats(one_two_one_view()) == set()


class TestChooseCell:
    class TestNormal:
        def test_성공_확실한_고양이가_있으면_반드시_고른다(self):
            assert choose_cell(single_certain_view(), Difficulty.NORMAL, random.Random(1)) == (1, 1)

        def test_성공_확실한_고양이가_없으면_안전이_확정된_칸은_빼고_고른다(self):
            # 3x3. (0,0)=1 이고 (1,1) 은 이미 찾았다 → (1,0)·(0,1) 은 안전 확정
            view = BoardView(size=3, numbers={(0, 0): 1}, found=frozenset({(1, 1)}), remaining=2)
            for seed in range(30):
                assert choose_cell(view, Difficulty.NORMAL, random.Random(seed)) not in {(1, 0), (0, 1)}

        def test_성공_안전한_칸밖에_없으면_그중에서_고른다(self):
            view = BoardView(size=2, numbers={(0, 0): 1}, found=frozenset({(1, 1)}), remaining=0)

            assert choose_cell(view, Difficulty.NORMAL, random.Random(1)) in {(1, 0), (0, 1)}

    class TestEasy:
        def test_성공_30퍼센트_안쪽이면_확실한_고양이를_고른다(self):
            assert choose_cell(single_certain_view(), Difficulty.EASY, FixedRandom(0.1)) == (1, 1)

        def test_성공_30퍼센트_밖이면_닫힌_칸_중_무작위로_고른다(self):
            choice = choose_cell(single_certain_view(), Difficulty.EASY, FixedRandom(0.9))

            assert choice == sorted(single_certain_view().closed_cells())[0]

    class TestHard:
        def test_성공_여러_숫자를_엮어_확정되는_고양이를_고른다(self):
            assert choose_cell(one_two_one_view(), Difficulty.HARD, random.Random(1)) in {(0, 1), (2, 1)}

        def test_성공_안전이_확정된_칸은_고르지_않는다(self):
            for seed in range(20):
                assert choose_cell(one_two_one_view(), Difficulty.HARD, random.Random(seed)) != (1, 1)

        def test_성공_확실한_칸이_없으면_고양이일_확률이_가장_높은_칸을_고른다(self):
            # 2x2, (0,0)=3 → 닫힌 세 칸이 모두 고양이(확률 1). remaining 를 3 으로 맞춘다.
            view = BoardView(size=2, numbers={(0, 0): 3}, found=frozenset(), remaining=3)

            assert choose_cell(view, Difficulty.HARD, random.Random(1)) in {(1, 0), (0, 1), (1, 1)}

        def test_성공_경계_칸이_아주_많아도_빠르게_닫힌_칸을_고른다(self):
            # 12x12 바둑판 모양으로 절반을 연다 → 72칸이 하나로 이어진 경계가 된다(근사 계산 경로)
            numbers = {(x, y): 1 for y in range(12) for x in range(12) if (x + y) % 2 == 0}
            view = BoardView(size=12, numbers=numbers, found=frozenset(), remaining=25)

            started = time.perf_counter()
            choice = choose_cell(view, Difficulty.HARD, random.Random(1))

            assert choice in view.closed_cells()
            assert time.perf_counter() - started < 1.0

        def test_성공_모순된_판이어도_오류_없이_닫힌_칸을_고른다(self):
            view = BoardView(size=3, numbers={(0, 0): 3}, found=frozenset(), remaining=1)

            assert choose_cell(view, Difficulty.HARD, random.Random(1)) in view.closed_cells()

    class TestAlways:
        @pytest.mark.parametrize("difficulty", list(Difficulty))
        def test_성공_어떤_난이도든_항상_닫힌_칸만_고른다(self, difficulty):
            view = one_two_one_view()
            for seed in range(30):
                assert choose_cell(view, difficulty, random.Random(seed)) in view.closed_cells()

        def test_실패_닫힌_칸이_없으면_오류다(self):
            view = BoardView(size=1, numbers={(0, 0): 0}, found=frozenset(), remaining=0)

            with pytest.raises(ValueError):
                choose_cell(view, Difficulty.HARD, random.Random(1))
