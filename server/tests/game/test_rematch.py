import pytest

from wheresmeow.game.domain.errors import NotAParticipant, RematchExpired
from wheresmeow.game.domain.rematch import REMATCH_WINDOW_MS, Rematch, RematchClosed

T0 = 1_000


def human_rematch() -> Rematch:
    return Rematch("g1", ("a", "b"))


class TestRematch:
    class TestRequest:
        def test_성공_한쪽만_요청하면_상대를_기다린다(self):
            rematch = human_rematch()

            assert rematch.request("a", T0) is False
            assert rematch.deadline_ms == T0 + REMATCH_WINDOW_MS
            assert rematch.closed is None

        def test_성공_상대가_수락하면_새_대국을_시작한다(self):
            rematch = human_rematch()
            rematch.request("a", T0)

            assert rematch.request("b", T0 + 1_000) is True
            assert rematch.closed is RematchClosed.STARTED

        def test_성공_같은_사람이_두_번_요청해도_한_번으로_센다(self):
            rematch = human_rematch()
            rematch.request("a", T0)

            assert rematch.request("a", T0 + 1) is False
            assert rematch.deadline_ms == T0 + REMATCH_WINDOW_MS  # 마감은 처음 요청 기준이다

        def test_성공_봇_대국은_봇이_즉시_수락한다(self):
            rematch = Rematch("g1", ("a", "bot:EASY"), bot_player_id="bot:EASY")

            assert rematch.request("a", T0) is True

        def test_실패_30초가_지나면_REMATCH_EXPIRED(self):
            rematch = human_rematch()
            rematch.request("a", T0)

            with pytest.raises(RematchExpired):
                rematch.request("b", T0 + REMATCH_WINDOW_MS)
            assert rematch.closed is RematchClosed.EXPIRED

        def test_실패_이미_시작했으면_다시_요청할_수_없다(self):
            rematch = human_rematch()
            rematch.request("a", T0)
            rematch.request("b", T0)

            with pytest.raises(RematchExpired):
                rematch.request("a", T0)

        def test_실패_참가자가_아니면_거부한다(self):
            with pytest.raises(NotAParticipant):
                human_rematch().request("stranger", T0)

    class TestDecline:
        def test_성공_거절하면_요청한_사람에게_알리고_닫는다(self):
            rematch = human_rematch()
            rematch.request("a", T0)

            assert rematch.decline("b") == ["a"]
            assert rematch.closed is RematchClosed.DECLINED
            with pytest.raises(RematchExpired):
                rematch.request("a", T0)

        def test_성공_요청이_없을_때_거절해도_닫힌다(self):
            rematch = human_rematch()

            assert rematch.decline("b") == []
            with pytest.raises(RematchExpired):
                rematch.request("a", T0)

        def test_성공_이미_닫혔으면_아무도_알리지_않는다(self):
            rematch = human_rematch()
            rematch.decline("b")

            assert rematch.decline("a") == []

    class TestLeave:
        def test_성공_결과_화면을_떠나면_상대에게_알리고_닫는다(self):
            rematch = human_rematch()

            assert rematch.leave("a") == ["b"]
            assert rematch.closed is RematchClosed.LEFT

        def test_성공_시작한_뒤에_떠나면_아무도_알리지_않는다(self):
            rematch = human_rematch()
            rematch.request("a", T0)
            rematch.request("b", T0)

            assert rematch.leave("a") == []
            assert rematch.closed is RematchClosed.STARTED

    class TestExpire:
        def test_성공_마감이_지난_요청은_두_사람에게_알리고_닫는다(self):
            rematch = human_rematch()
            rematch.request("a", T0)

            assert rematch.expire(T0 + REMATCH_WINDOW_MS) == ["a", "b"]
            assert rematch.closed is RematchClosed.EXPIRED

        def test_성공_마감_전이거나_이미_닫혔으면_아무것도_하지_않는다(self):
            rematch = human_rematch()
            rematch.request("a", T0)

            assert rematch.expire(T0 + REMATCH_WINDOW_MS - 1) == []
            rematch.decline("b")
            assert rematch.expire(T0 + REMATCH_WINDOW_MS) == []
