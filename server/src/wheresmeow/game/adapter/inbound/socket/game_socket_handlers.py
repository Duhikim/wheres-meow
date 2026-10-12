from collections.abc import Callable

from flask_socketio import SocketIO
from pydantic import BaseModel, ConfigDict, Field, StrictInt

from wheresmeow.game.application.port.inbound import ForfeitUseCase, RevealCellUseCase
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
