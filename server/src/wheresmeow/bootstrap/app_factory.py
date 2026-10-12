from flask import Flask, jsonify, request
from flask_socketio import ConnectionRefusedError, SocketIO, join_room

from wheresmeow.account.adapter.inbound.web.account_api import create_account_blueprint
from wheresmeow.bootstrap.config import AppConfig
from wheresmeow.bootstrap.container import Container, build_container
from wheresmeow.bootstrap.error_handlers import register_http_error_handlers, register_socket_error_handler
from wheresmeow.bootstrap.static_site import register_static_site
from wheresmeow.game.adapter.inbound.socket.game_socket_handlers import register_game_socket_handlers
from wheresmeow.game.adapter.inbound.web.game_api import create_game_blueprint
from wheresmeow.room.adapter.inbound.socket.room_socket_handlers import register_room_socket_handlers
from wheresmeow.room.adapter.inbound.web.room_api import create_room_blueprint
from wheresmeow.shared.errors import DomainError
from wheresmeow.shared.socket_rooms import player_room


def create_app(config: AppConfig | None = None, **overrides) -> tuple[Flask, SocketIO]:
    """overrides 는 build_container 의 키워드 인자(clock, turn_timer 등)로 그대로 전달된다."""
    config = config or AppConfig.from_env()
    app = Flask(__name__, static_folder=None)  # 정적 파일은 register_static_site 가 맡는다
    app.config["SECRET_KEY"] = config.secret_key
    socketio = SocketIO(app, async_mode=config.async_mode)

    container = build_container(config, socketio, **overrides)
    app.extensions["wheresmeow"] = container

    register_http_error_handlers(app)
    register_socket_error_handler(socketio)
    _register_connection_handlers(socketio, container)

    identity = container.http_identity
    app.register_blueprint(
        create_account_blueprint(
            container.guest_service, container.guest_service, container.guest_service, identity.current_player
        )
    )
    app.register_blueprint(
        create_room_blueprint(container.room_service, container.room_service, identity.current_player_id)
    )
    app.register_blueprint(create_game_blueprint(container.game_service, identity.current_player_id))

    sessions = container.socket_sessions
    register_room_socket_handlers(
        socketio, container.room_service, container.room_service, sessions.current_player_id
    )
    register_game_socket_handlers(
        socketio, container.game_service, container.game_service, container.game_service, sessions.current_player_id
    )

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    if config.static_dir is not None:
        register_static_site(app, config.static_dir)  # 다른 라우트를 모두 등록한 뒤에 붙인다
    return app, socketio


def _register_connection_handlers(socketio: SocketIO, container: Container) -> None:
    @socketio.on("connect")
    def on_connect(auth):
        token = auth.get("token") if isinstance(auth, dict) else None
        try:
            player = container.guest_service.authenticate(token or "")
        except DomainError as error:
            raise ConnectionRefusedError(error.code) from error
        container.socket_sessions.bind(request.sid, player.id)
        join_room(player_room(player.id))

    @socketio.on("disconnect")
    def on_disconnect(*_args):
        container.socket_sessions.unbind(request.sid)
