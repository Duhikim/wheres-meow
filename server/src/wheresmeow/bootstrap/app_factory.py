from flask import Flask, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import ConnectionRefusedError, SocketIO, join_room
from werkzeug.middleware.proxy_fix import ProxyFix

from wheresmeow.account.adapter.inbound.web.account_api import create_account_blueprint
from wheresmeow.account.adapter.inbound.web.auth_api import CookiePolicy, create_auth_blueprint
from wheresmeow.account.adapter.inbound.web.oauth_client import AuthlibOAuthClient, OAuthClient
from wheresmeow.bootstrap.config import AppConfig
from wheresmeow.bootstrap.container import Container, build_container
from wheresmeow.bootstrap.error_handlers import register_http_error_handlers, register_socket_error_handler
from wheresmeow.bootstrap.static_site import register_static_site
from wheresmeow.bot.adapter.inbound.socket.bot_socket_handlers import register_bot_socket_handlers
from wheresmeow.bot.adapter.inbound.web.bot_api import create_bot_blueprint
from wheresmeow.game.adapter.inbound.socket.game_socket_handlers import register_game_socket_handlers
from wheresmeow.game.adapter.inbound.web.game_api import create_game_blueprint
from wheresmeow.matchmaking.adapter.inbound.match_socket_handlers import register_match_socket_handlers
from wheresmeow.practice.adapter.inbound.web.practice_api import create_practice_blueprint
from wheresmeow.rating.adapter.inbound.web.rating_api import create_rating_blueprint
from wheresmeow.room.adapter.inbound.socket.room_socket_handlers import register_room_socket_handlers
from wheresmeow.room.adapter.inbound.web.room_api import create_room_blueprint
from wheresmeow.shared.errors import DomainError
from wheresmeow.shared.socket_rooms import player_room


def create_app(config: AppConfig | None = None, **overrides) -> tuple[Flask, SocketIO]:
    """overrides 는 build_container 의 키워드 인자(clock, turn_timer 등)로 그대로 전달된다.

    oauth_client 만은 Flask 앱이 있어야 만들 수 있어서 여기서 받는다(테스트는 가짜를 넘긴다).
    """
    config = config or AppConfig.from_env()
    app = Flask(__name__, static_folder=None)  # 정적 파일은 register_static_site 가 맡는다
    app.config["SECRET_KEY"] = config.secret_key
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"  # 소셜 로그인 state 를 담는 세션 쿠키
    app.config["SESSION_COOKIE_SECURE"] = config.is_production
    if config.is_production:
        # Railway 프록시 뒤에서 실제 IP(로그인 횟수 제한)와 https(소셜 로그인 콜백 주소)를 알기 위해
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)  # type: ignore[method-assign]
    socketio = SocketIO(app, async_mode=config.async_mode)

    oauth_client: OAuthClient = overrides.pop("oauth_client", None) or AuthlibOAuthClient(
        app, {provider: (client_id, secret) for provider, client_id, secret in config.oauth}
    )
    limiter = Limiter(get_remote_address, app=app, storage_uri="memory://")
    container = build_container(config, socketio, **overrides)
    app.extensions["wheresmeow"] = container

    register_http_error_handlers(app)
    register_socket_error_handler(socketio)
    _register_connection_handlers(socketio, container)

    identity = container.http_identity
    app.register_blueprint(
        create_account_blueprint(
            container.guest_service,
            container.guest_service,
            container.authenticator,
            container.member_service.change_nickname,
            identity.current_player,
        )
    )
    app.register_blueprint(
        create_auth_blueprint(
            container.member_service,
            oauth_client,
            CookiePolicy(secure=config.is_production),
            limiter.limit("10 per minute"),  # 로그인·가입은 IP 당 분당 10회(스펙 4.4)
        )
    )
    app.register_blueprint(
        create_room_blueprint(container.room_service, container.room_service, identity.current_player_id)
    )
    app.register_blueprint(create_game_blueprint(container.game_service, identity.current_player_id))
    app.register_blueprint(create_bot_blueprint(container.bot_service, identity.current_player_id))
    app.register_blueprint(create_rating_blueprint(container.rating_query_service, container.rating_query_service))
    app.register_blueprint(
        create_practice_blueprint(container.practice_service, container.practice_service, identity.current_player_id)
    )

    sessions = container.socket_sessions
    register_room_socket_handlers(
        socketio, container.room_service, container.room_service, sessions.current_player_id
    )
    register_bot_socket_handlers(socketio, container.bot_service, sessions.current_player_id)
    register_match_socket_handlers(
        socketio, container.matchmaking_service, container.matchmaking_service, sessions.current_player_id
    )
    register_game_socket_handlers(
        socketio,
        container.game_service,
        container.game_service,
        container.game_service,
        container.rematch_service,
        sessions.current_player_id,
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
            player = container.authenticator.authenticate(token or "")
        except DomainError as error:
            raise ConnectionRefusedError(error.code) from error
        container.socket_sessions.bind(request.sid, player.id)
        join_room(player_room(player.id))

    @socketio.on("disconnect")
    def on_disconnect(*_args):
        last_player_id = container.socket_sessions.unbind(request.sid)
        if last_player_id is not None:
            # 그 플레이어의 연결이 모두 끊기면 대기열에서 뺀다(스펙 4.3). 다른 연결이 남아 있으면 그대로 둔다.
            container.matchmaking_service.leave_match(last_player_id)
