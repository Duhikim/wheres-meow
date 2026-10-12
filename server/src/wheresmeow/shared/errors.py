"""모든 도메인이 공유하는 예외 기반 클래스."""


class DomainError(Exception):
    """오류 코드가 붙은 도메인 규칙 위반. 하위 클래스는 code 만 바꾼다."""

    code: str = "INTERNAL"

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.code
        super().__init__(self.message)


class InvalidInput(DomainError):
    code = "INVALID_INPUT"


class Unauthorized(DomainError):
    code = "UNAUTHORIZED"
