from dataclasses import dataclass
from enum import StrEnum

from wheresmeow.shared.errors import DomainError, InvalidInput

NICKNAME_MIN_LENGTH = 2
NICKNAME_MAX_LENGTH = 12
DEFAULT_SKIN_1P = 16
DEFAULT_SKIN_2P = 17
# game 도메인의 skins.ALLOWED_SKINS 와 같은 목록이다. 도메인끼리 import 하지 않으므로 따로 둔다(스펙 4.4).
ALLOWED_SKINS = frozenset({9, 10, 11, 12, 16, 17, 18, 19, 20, 21})


class InvalidSkin(DomainError):
    code = "INVALID_SKIN"


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

    def change_skins(self, skin_1p: int, skin_2p: int) -> None:
        """1P·2P 스킨을 바꾼다. 둘 다 허용 목록에 있고 서로 달라야 한다(대국에서 겹침을 피하는 근거)."""
        if skin_1p not in ALLOWED_SKINS or skin_2p not in ALLOWED_SKINS:
            raise InvalidSkin(f"허용하지 않는 스킨입니다: {skin_1p}, {skin_2p}")
        if skin_1p == skin_2p:
            raise InvalidSkin("1P 와 2P 스킨은 서로 달라야 합니다")
        self.skin_1p = skin_1p
        self.skin_2p = skin_2p
