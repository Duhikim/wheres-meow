"""고양이 스킨 목록과 대국 시 스킨 배정 규칙."""

from dataclasses import dataclass

from wheresmeow.game.domain.errors import InvalidSkin

ALLOWED_SKINS = frozenset({9, 10, 11, 12, 16, 17, 18, 19, 20, 21})
DEFAULT_SKIN_1P = 16
DEFAULT_SKIN_2P = 17


@dataclass(frozen=True)
class SkinPreference:
    skin_1p: int = DEFAULT_SKIN_1P
    skin_2p: int = DEFAULT_SKIN_2P

    def __post_init__(self) -> None:
        if self.skin_1p not in ALLOWED_SKINS or self.skin_2p not in ALLOWED_SKINS:
            raise InvalidSkin(f"허용하지 않는 스킨입니다: {self.skin_1p}, {self.skin_2p}")
        if self.skin_1p == self.skin_2p:
            raise InvalidSkin("1P 와 2P 스킨은 서로 달라야 합니다")


def assign_skins(priority: SkinPreference, other: SkinPreference) -> tuple[int, int]:
    """우선권자는 항상 1P. 상대는 1P 가 겹칠 때만 2P 를 쓴다.

    1P 와 2P 가 항상 다르므로 결과 두 값은 반드시 서로 다르다.
    """
    other_skin = other.skin_2p if other.skin_1p == priority.skin_1p else other.skin_1p
    return priority.skin_1p, other_skin
