from wheresmeow.shared.errors import DomainError, InvalidInput, Unauthorized


class TestDomainError:
    class TestInit:
        def test_성공_메시지가_없으면_코드를_메시지로_쓴다(self):
            error = InvalidInput()

            assert error.code == "INVALID_INPUT"
            assert error.message == "INVALID_INPUT"

        def test_성공_메시지를_주면_그대로_보존한다(self):
            error = Unauthorized("토큰이 만료되었습니다")

            assert error.code == "UNAUTHORIZED"
            assert error.message == "토큰이 만료되었습니다"

        def test_성공_기본_코드는_INTERNAL_이다(self):
            assert DomainError().code == "INTERNAL"
