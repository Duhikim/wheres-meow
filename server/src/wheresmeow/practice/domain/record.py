"""혼자 연습(클래식 지뢰찾기)의 최고 기록 규칙. 판 진행은 브라우저가 하고, 서버는 클리어 시간만 받는다."""

from enum import StrEnum

from wheresmeow.shared.errors import InvalidInput

MIN_ELAPSED_MS = 1_000  # 첫 칸 하나로 끝나는 판은 없다. 이보다 빠르면 조작된 값으로 본다
MAX_ELAPSED_MS = 24 * 60 * 60 * 1_000


class Difficulty(StrEnum):
    BEGINNER = "BEGINNER"  # 9×9, 고양이 10
    INTERMEDIATE = "INTERMEDIATE"  # 12×12, 고양이 25
    EXPERT = "EXPERT"  # 12×16, 고양이 40


def parse_difficulty(raw: str) -> Difficulty:
    try:
        return Difficulty(raw)
    except ValueError as error:
        raise InvalidInput(f"알 수 없는 난이도입니다: {raw}") from error


def validate_elapsed(elapsed_ms: int) -> int:
    if not MIN_ELAPSED_MS <= elapsed_ms <= MAX_ELAPSED_MS:
        raise InvalidInput(f"클리어 시간이 올바르지 않습니다: {elapsed_ms}ms")
    return elapsed_ms
