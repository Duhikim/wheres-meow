from dataclasses import dataclass
from typing import Protocol

from wheresmeow.room.domain.room import Room


@dataclass(frozen=True)
class RoomJoinOutcome:
    room: Room
    game_id: str | None  # None 이면 방장이 대기 중


class CreateRoomUseCase(Protocol):
    def create_room(self, host_id: str) -> Room: ...


class GetRoomUseCase(Protocol):
    def get_room(self, code: str) -> Room: ...


class JoinRoomUseCase(Protocol):
    def join(self, code: str, player_id: str) -> RoomJoinOutcome: ...


class CancelRoomUseCase(Protocol):
    def cancel(self, code: str, player_id: str) -> None: ...
