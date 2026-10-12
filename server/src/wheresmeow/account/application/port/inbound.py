from dataclasses import dataclass
from typing import Protocol

from wheresmeow.account.domain.player import Player


@dataclass(frozen=True)
class GuestCredentials:
    player: Player
    token: str


class CreateGuestUseCase(Protocol):
    def create_guest(self, nickname: str) -> GuestCredentials: ...


class AuthenticateUseCase(Protocol):
    def authenticate(self, token: str) -> Player:
        """토큰이 유효하지 않거나 플레이어가 없으면 Unauthorized."""
        ...


class GetPlayerUseCase(Protocol):
    def get_player(self, player_id: str) -> Player: ...


class ChangeSkinsUseCase(Protocol):
    def change_skins(self, player_id: str, skin_1p: int, skin_2p: int) -> Player: ...
