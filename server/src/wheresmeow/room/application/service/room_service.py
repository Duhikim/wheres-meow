import random
import threading
from collections.abc import Callable

from wheresmeow.room.application.port.inbound import RoomJoinOutcome
from wheresmeow.room.application.port.outbound import GameStarter, PlayerDirectory, RoomStore
from wheresmeow.room.domain.room import JoinResult, Room, RoomNotFound, generate_room_code
from wheresmeow.shared.clock import Clock

MAX_CODE_ATTEMPTS = 20


class RoomService:
    """CreateRoom·GetRoom·JoinRoom·CancelRoom 유스케이스 구현."""

    def __init__(
        self,
        store: RoomStore,
        players: PlayerDirectory,
        game_starter: GameStarter,
        clock: Clock,
        code_factory: Callable[[], str] = lambda: generate_room_code(random.SystemRandom()),
    ) -> None:
        self._store = store
        self._players = players
        self._game_starter = game_starter
        self._clock = clock
        self._code_factory = code_factory
        self._guard = threading.Lock()  # 같은 방에 두 사람이 동시에 들어오는 경쟁을 막는다

    def create_room(self, host_id: str) -> Room:
        self._players.profile(host_id)  # 없는 플레이어면 여기서 실패한다
        with self._guard:
            for _ in range(MAX_CODE_ATTEMPTS):
                code = self._code_factory()
                if self._store.get(code) is None:
                    room = Room(code, host_id, self._clock.now_ms())
                    self._store.save(room)
                    return room
        raise RuntimeError("사용하지 않는 방 코드를 찾지 못했습니다")

    def get_room(self, code: str) -> Room:
        room = self._require(code)
        room.ensure_open(self._clock.now_ms())
        return room

    def join(self, code: str, player_id: str) -> RoomJoinOutcome:
        with self._guard:
            room = self._require(code)
            if room.admit(player_id, self._clock.now_ms()) is JoinResult.HOST_WAITING:
                return RoomJoinOutcome(room, None)
            host = self._players.profile(room.host_id)
            guest = self._players.profile(player_id)
            game_id = self._game_starter.start_invite_game(host, guest)
            room.start(player_id, game_id)
            self._store.save(room)
            return RoomJoinOutcome(room, game_id)

    def cancel(self, code: str, player_id: str) -> None:
        with self._guard:
            room = self._require(code)
            room.cancel(player_id)
            self._store.save(room)

    def _require(self, code: str) -> Room:
        room = self._store.get(code.upper())
        if room is None:
            raise RoomNotFound(f"방을 찾을 수 없습니다: {code}")
        return room
