import pytest

from wheresmeow.rating.domain.elo import INITIAL_RATING, K_FACTOR, Outcome, expected_score, rate


class TestExpectedScore:
    class TestCompute:
        def test_성공_같은_레이팅이면_0_5다(self):
            assert expected_score(1000, 1000) == pytest.approx(0.5)

        def test_성공_400점_높으면_약_0_91이다(self):
            assert expected_score(1400, 1000) == pytest.approx(10 / 11)


class TestRate:
    class TestOutcome:
        def test_성공_같은_레이팅에서_이기면_K의_절반만큼_오르고_진_쪽은_그만큼_내린다(self):
            assert rate(1000, 1000, Outcome.FIRST_WINS) == (1016, 984)

        def test_성공_무승부면_같은_레이팅은_그대로다(self):
            assert rate(1000, 1000, Outcome.DRAW) == (1000, 1000)

        def test_성공_약한_쪽이_이기면_많이_오른다(self):
            weak, strong = rate(1000, 1400, Outcome.FIRST_WINS)

            assert weak - 1000 == round(K_FACTOR * (1 - expected_score(1000, 1400)))
            assert weak - 1000 > 16

        def test_성공_두_사람의_변화량_합은_0이다(self):
            a, b = rate(1137, 982, Outcome.SECOND_WINS)

            assert (a - 1137) + (b - 982) == 0

    class TestInitial:
        def test_성공_초기_레이팅은_1000이다(self):
            assert INITIAL_RATING == 1000
