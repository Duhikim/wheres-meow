"""회원(자체 가입·소셜 로그인) 규칙."""

import re

from wheresmeow.shared.errors import DomainError, InvalidInput

USERNAME_PATTERN = re.compile(r"^[a-z0-9_]{4,20}$")
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128


class UsernameTaken(DomainError):
    code = "USERNAME_TAKEN"


class NicknameTaken(DomainError):
    code = "NICKNAME_TAKEN"


class InvalidCredentials(DomainError):
    """아이디가 없는지 비밀번호가 틀렸는지 구분해 알려 주지 않는다."""

    code = "INVALID_CREDENTIALS"


class ProviderDisabled(DomainError):
    code = "PROVIDER_DISABLED"


def validate_username(raw: str) -> str:
    if not USERNAME_PATTERN.fullmatch(raw):
        raise InvalidInput("아이디는 4~20자의 영문 소문자·숫자·밑줄이어야 합니다")
    return raw


def validate_password(raw: str) -> str:
    if not PASSWORD_MIN_LENGTH <= len(raw) <= PASSWORD_MAX_LENGTH:
        raise InvalidInput(f"비밀번호는 {PASSWORD_MIN_LENGTH}~{PASSWORD_MAX_LENGTH}자여야 합니다")
    return raw
