"""어댑터를 포트에 연결한다. 테스트는 키워드 인자로 일부 어댑터를 바꿔 끼운다."""

from collections.abc import Callable
from dataclasses import dataclass

from flask_socketio import SocketIO

from wheresmeow.account.adapter.outbound.persistence.sql_player_store import SqlPlayerStore
from wheresmeow.account.adapter.outbound.token.signed_token_issuer import SignedTokenIssuer
from wheresmeow.account.application.service.guest_service import GuestService
from wheresmeow.bootstrap.config import AppConfig
from wheresmeow.bootstrap.identity import HttpIdentity, SocketSessions
from wheresmeow.bootstrap.migrations import run_migrations
from wheresmeow.game.adapter.outbound.memory.in_memory_game_store import InMemoryGameStore
from wheresmeow.game.adapter.outbound.persistence.sql_game_result_recorder import SqlGameResultRecorder
from wheresmeow.game.adapter.outbound.socket.socketio_game_event_publisher import SocketIOGameEventPublisher
from wheresmeow.game.adapter.outbound.timer.background_turn_timer import BackgroundTurnTimer
from wheresmeow.game.application.port.outbound import TurnTimer
from wheresmeow.game.application.service.game_service import GameService
from wheresmeow.game.domain.board import MineLayoutGenerator, RandomMineLayoutGenerator, SeededMineLayoutGenerator
from wheresmeow.room.adapter.outbound.account.account_player_directory import AccountPlayerDirectory
from wheresmeow.room.adapter.outbound.game.game_starter_adapter import GameStarterAdapter
from wheresmeow.room.adapter.outbound.memory.in_memory_room_store import InMemoryRoomStore
from wheresmeow.room.application.service.room_service import RoomService
from wheresmeow.shared.clock import Clock, SystemClock
from wheresmeow.shared.persistence.database import Database


@dataclass(frozen=True)
class Container:
    config: AppConfig
    database: Database
    guest_service: GuestService
    game_service: GameService
    room_service: RoomService
    http_identity: HttpIdentity
    socket_sessions: SocketSessions


def build_container(
    config: AppConfig,
    socketio: SocketIO,
    *,
    database: Database | None = None,
    clock: Clock | None = None,
    turn_timer: TurnTimer | None = None,
    layout_generator: MineLayoutGenerator | None = None,
    first_seat_chooser: Callable[[], int] | None = None,
) -> Container:
    clock = clock or SystemClock()
    if database is None:
        # 주입받지 않았으면 설정의 DB 에 연결하고 스키마를 최신으로 맞춘다(테스트는 미리 맞춘 DB 를 넘긴다)
        database = Database(config.database_url)
        run_migrations(database)
    if layout_generator is None:
        layout_generator = (
            SeededMineLayoutGenerator(config.test_seed)
            if config.test_seed is not None
            else RandomMineLayoutGenerator()
        )

    guest_service = GuestService(SqlPlayerStore(database, clock), SignedTokenIssuer(config.secret_key))

    game_options = {"first_seat_chooser": first_seat_chooser} if first_seat_chooser else {}
    game_service = GameService(
        InMemoryGameStore(),
        SocketIOGameEventPublisher(socketio),
        turn_timer or BackgroundTurnTimer(socketio, clock),
        layout_generator,
        clock,
        recorder=SqlGameResultRecorder(database, clock),
        **game_options,
    )

    room_service = RoomService(
        InMemoryRoomStore(),
        AccountPlayerDirectory(guest_service),
        GameStarterAdapter(game_service),
        clock,
    )

    return Container(
        config=config,
        database=database,
        guest_service=guest_service,
        game_service=game_service,
        room_service=room_service,
        http_identity=HttpIdentity(guest_service),
        socket_sessions=SocketSessions(),
    )
