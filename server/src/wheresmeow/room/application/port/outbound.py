from dataclasses import dataclass
from typing import Protocol

from wheresmeow.room.domain.room import Room


@dataclass(frozen=True)
class PlayerProfile:
    player_id: str
    nickname: str
    skin_1p: int
    skin_2p: int


class RoomStore(Protocol):
    def save(self, room: Room) -> None: ...

    def get(self, code: str) -> Room | None: ...


class PlayerDirectory(Protocol):
    def profile(self, player_id: str) -> PlayerProfile: ...


class GameStarter(Protocol):
    def start_invite_game(self, host: PlayerProfile, guest: PlayerProfile) -> str:
        """대국을 시작하고 game_id 를 돌려준다. 방장이 스킨 우선권을 갖는다."""
        ...
