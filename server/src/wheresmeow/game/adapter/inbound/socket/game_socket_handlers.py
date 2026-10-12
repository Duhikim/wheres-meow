from collections.abc import Callable

from flask_socketio import SocketIO, emit
from pydantic import BaseModel, ConfigDict, Field, StrictInt

from wheresmeow.game.adapter.outbound.socket.payloads import snapshot_payload
from wheresmeow.game.application.port.inbound import (
    ForfeitUseCase,
    GetGameUseCase,
    RematchUseCase,
    RevealCellUseCase,
)
from wheresmeow.shared.payload import parse_payload


class RevealRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    gameId: str = Field(min_length=1)
    x: StrictInt
    y: StrictInt


class GameRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    gameId: str = Field(min_length=1)


def register_game_socket_handlers(
    socketio: SocketIO,
    reveal: RevealCellUseCase,
    forfeit: ForfeitUseCase,
    get_game: GetGameUseCase,
    rematch: RematchUseCase,
    current_player_id: Callable[[], str],
) -> None:
    """결과는 GameEventPublisher 가 두 참가자에게 보낸다. 실패는 공통 오류 핸들러가 error 로 보낸다."""

    @socketio.on("game:reveal")
    def on_reveal(data):
        request = parse_payload(RevealRequest, data)
        reveal.reveal(request.gameId, current_player_id(), request.x, request.y)

    @socketio.on("game:forfeit")
    def on_forfeit(data):
        request = parse_payload(GameRequest, data)
        forfeit.forfeit(request.gameId, current_player_id())

    @socketio.on("game:rematch-request")
    def on_rematch_request(data):
        request = parse_payload(GameRequest, data)
        rematch.request_rematch(request.gameId, current_player_id())

    @socketio.on("game:rematch-decline")
    def on_rematch_decline(data):
        request = parse_payload(GameRequest, data)
        rematch.decline_rematch(request.gameId, current_player_id())

    @socketio.on("game:leave-result")
    def on_leave_result(data):
        request = parse_payload(GameRequest, data)
        rematch.leave_result(request.gameId, current_player_id())

    @socketio.on("game:sync")
    def on_sync(data):
        """재접속·새로고침·이벤트 누락 시 현재 상태 전체를 요청한 소켓에만 보낸다."""
        request = parse_payload(GameRequest, data)
        player_id = current_player_id()
        game = get_game.get_game(request.gameId, player_id)
        emit("game:state", snapshot_payload(game, game.seat_of(player_id)))
