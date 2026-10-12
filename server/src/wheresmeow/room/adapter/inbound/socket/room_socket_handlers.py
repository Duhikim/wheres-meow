from collections.abc import Callable

from flask_socketio import SocketIO, emit
from pydantic import BaseModel, ConfigDict, Field

from wheresmeow.room.adapter.inbound.web.room_api import room_payload
from wheresmeow.room.application.port.inbound import CancelRoomUseCase, JoinRoomUseCase
from wheresmeow.shared.payload import parse_payload


class RoomRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str = Field(min_length=6, max_length=6)


def register_room_socket_handlers(
    socketio: SocketIO,
    join_room: JoinRoomUseCase,
    cancel_room: CancelRoomUseCase,
    current_player_id: Callable[[], str],
) -> None:
    @socketio.on("room:join")
    def on_join(data):
        request = parse_payload(RoomRequest, data)
        outcome = join_room.join(request.code, current_player_id())
        if outcome.game_id is None:
            emit("room:waiting", room_payload(outcome.room))
        # 대국이 시작되면 game:started 는 GameEventPublisher 가 두 사람에게 보낸다

    @socketio.on("room:cancel")
    def on_cancel(data):
        request = parse_payload(RoomRequest, data)
        cancel_room.cancel(request.code, current_player_id())
        emit("room:cancelled", {"code": request.code.upper()})
