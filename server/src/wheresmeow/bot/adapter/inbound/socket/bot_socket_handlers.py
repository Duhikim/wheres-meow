from collections.abc import Callable

from flask_socketio import SocketIO
from pydantic import BaseModel, ConfigDict

from wheresmeow.bot.application.service.bot_service import BotService
from wheresmeow.shared.payload import parse_payload


class StartBotRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    difficulty: str


def register_bot_socket_handlers(socketio: SocketIO, bots: BotService, current_player_id: Callable[[], str]) -> None:
    @socketio.on("bot:start")
    def on_start(data):
        request = parse_payload(StartBotRequest, data)
        bots.start_bot_game(current_player_id(), request.difficulty)
        # 대국이 시작되면 game:started 는 GameEventPublisher 가 보낸다
