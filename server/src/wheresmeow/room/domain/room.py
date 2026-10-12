"""초대 방. 방장과 상대 한 명이 모이면 대국을 시작한다."""

import random
from dataclasses import dataclass
from enum import StrEnum

from wheresmeow.shared.errors import DomainError

ROOM_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # 0·O·1·I 제외
ROOM_CODE_LENGTH = 6
ROOM_TTL_MS = 10 * 60 * 1000


class RoomNotFound(DomainError):
    code = "ROOM_NOT_FOUND"


class RoomFull(DomainError):
    code = "ROOM_FULL"


class RoomExpired(DomainError):
    code = "ROOM_EXPIRED"


class NotRoomHost(DomainError):
    code = "NOT_ROOM_HOST"


def generate_room_code(rng: random.Random) -> str:
    return "".join(rng.choice(ROOM_CODE_ALPHABET) for _ in range(ROOM_CODE_LENGTH))


class RoomStatus(StrEnum):
    WAITING = "WAITING"
    STARTED = "STARTED"
    CANCELLED = "CANCELLED"


class JoinResult(StrEnum):
    HOST_WAITING = "HOST_WAITING"  # 방장이 들어와 상대를 기다린다
    OPPONENT_ARRIVED = "OPPONENT_ARRIVED"  # 상대가 왔으니 대국을 시작해야 한다


@dataclass
class Room:
    code: str
    host_id: str
    created_at_ms: int
    status: RoomStatus = RoomStatus.WAITING
    guest_id: str | None = None
    game_id: str | None = None

    @property
    def expires_at_ms(self) -> int:
        return self.created_at_ms + ROOM_TTL_MS

    def ensure_open(self, now_ms: int) -> None:
        if self.status is RoomStatus.CANCELLED or (
            self.status is RoomStatus.WAITING and now_ms >= self.expires_at_ms
        ):
            raise RoomExpired(f"만료되었거나 취소된 방입니다: {self.code}")

    def admit(self, player_id: str, now_ms: int) -> JoinResult:
        """입장 판정만 한다. 대국 시작에 성공한 뒤 start() 로 상태를 바꾼다."""
        self.ensure_open(now_ms)
        if self.status is RoomStatus.STARTED:
            raise RoomFull(f"이미 대국이 시작된 방입니다: {self.code}")
        if player_id == self.host_id:
            return JoinResult.HOST_WAITING
        return JoinResult.OPPONENT_ARRIVED

    def start(self, guest_id: str, game_id: str) -> None:
        if self.status is not RoomStatus.WAITING:
            raise RoomFull(f"이미 대국이 시작된 방입니다: {self.code}")
        self.status = RoomStatus.STARTED
        self.guest_id = guest_id
        self.game_id = game_id

    def cancel(self, player_id: str) -> None:
        if player_id != self.host_id:
            raise NotRoomHost("방장만 방을 취소할 수 있습니다")
        if self.status is RoomStatus.WAITING:
            self.status = RoomStatus.CANCELLED
