import threading

from wheresmeow.room.domain.room import Room


class InMemoryRoomStore:
    """만료된 방도 남아 있다. 1단계에서는 메모리 정리를 하지 않는다(재시작 시 비워짐)."""

    def __init__(self) -> None:
        self._rooms: dict[str, Room] = {}
        self._guard = threading.Lock()

    def save(self, room: Room) -> None:
        with self._guard:
            self._rooms[room.code] = room

    def get(self, code: str) -> Room | None:
        with self._guard:
            return self._rooms.get(code)
