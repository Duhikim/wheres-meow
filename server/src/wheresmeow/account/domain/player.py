from dataclasses import dataclass
from enum import StrEnum

from wheresmeow.shared.errors import InvalidInput

NICKNAME_MIN_LENGTH = 2
NICKNAME_MAX_LENGTH = 12
DEFAULT_SKIN_1P = 16
DEFAULT_SKIN_2P = 17


class PlayerKind(StrEnum):
    MEMBER = "MEMBER"
    GUEST = "GUEST"


def normalize_nickname(raw: str) -> str:
    nickname = raw.strip()
    if not NICKNAME_MIN_LENGTH <= len(nickname) <= NICKNAME_MAX_LENGTH:
        raise InvalidInput(
            f"닉네임은 {NICKNAME_MIN_LENGTH}~{NICKNAME_MAX_LENGTH}자여야 합니다: {nickname!r}"
        )
    return nickname


@dataclass
class Player:
    id: str
    kind: PlayerKind
    nickname: str
    skin_1p: int = DEFAULT_SKIN_1P
    skin_2p: int = DEFAULT_SKIN_2P
