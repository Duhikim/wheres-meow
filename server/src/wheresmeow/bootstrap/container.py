"""어댑터를 포트에 연결한다. 테스트는 키워드 인자로 일부 어댑터를 바꿔 끼운다."""

from collections.abc import Callable
from dataclasses import dataclass

from flask_socketio import SocketIO

from wheresmeow.account.adapter.outbound.persistence.sql_account_store import SqlAccountStore
from wheresmeow.account.adapter.outbound.persistence.sql_player_store import SqlPlayerStore
from wheresmeow.account.adapter.outbound.persistence.sql_refresh_token_store import SqlRefreshTokenStore
from wheresmeow.account.adapter.outbound.token.argon2_password_hasher import Argon2PasswordHasher
from wheresmeow.account.adapter.outbound.token.jwt_access_token_issuer import JwtAccessTokenIssuer
from wheresmeow.account.adapter.outbound.token.signed_token_issuer import SignedTokenIssuer
from wheresmeow.account.application.service.authenticator import Authenticator
from wheresmeow.account.application.service.guest_service import GuestService
from wheresmeow.account.application.service.member_service import MemberService
from wheresmeow.bootstrap.config import AppConfig
from wheresmeow.bot.adapter.inbound.game_events.bot_turn_driver import BotTurnDriver, Scheduler, socketio_scheduler
from wheresmeow.bot.adapter.outbound.account.account_human_directory import AccountHumanDirectory
from wheresmeow.bot.adapter.outbound.game.bot_game_starter_adapter import BotGameStarterAdapter
from wheresmeow.bot.adapter.outbound.persistence.bot_record_contributor import BotRecordContributor
from wheresmeow.bot.adapter.outbound.persistence.sql_bot_record_reader import SqlBotRecordReader
from wheresmeow.bot.application.service.bot_service import BotService
from wheresmeow.bootstrap.identity import HttpIdentity, SocketSessions
from wheresmeow.bootstrap.migrations import run_migrations
from wheresmeow.game.adapter.outbound.composite_publisher import CompositeGameEventPublisher
from wheresmeow.game.adapter.outbound.memory.in_memory_game_store import InMemoryGameStore
from wheresmeow.game.adapter.outbound.persistence.sql_game_result_recorder import SqlGameResultRecorder
from wheresmeow.game.adapter.outbound.socket.socketio_game_event_publisher import SocketIOGameEventPublisher
from wheresmeow.game.adapter.outbound.timer.background_turn_timer import BackgroundTurnTimer
from wheresmeow.game.application.port.outbound import TurnTimer
from wheresmeow.game.adapter.outbound.socket.socketio_rematch_notifier import SocketIORematchNotifier
from wheresmeow.game.application.service.game_service import GameService
from wheresmeow.game.application.service.rematch_service import RematchService
from wheresmeow.game.domain.board import MineLayoutGenerator, RandomMineLayoutGenerator, SeededMineLayoutGenerator
from wheresmeow.matchmaking.adapter.inbound.match_ticker import Repeater, socketio_repeater
from wheresmeow.matchmaking.adapter.outbound.adapters import (
    AccountPlayerDirectory as MatchPlayerDirectory,
)
from wheresmeow.matchmaking.adapter.outbound.adapters import (
    MatchGameStarterAdapter,
    RatingLookupAdapter,
    SocketIOMatchNotifier,
)
from wheresmeow.matchmaking.application.service.matchmaking_service import MatchmakingService
from wheresmeow.rating.adapter.outbound.account.account_player_directory import (
    AccountPlayerDirectory as RatingPlayerDirectory,
)
from wheresmeow.rating.adapter.outbound.bot.bot_record_source_adapter import BotRecordSourceAdapter
from wheresmeow.rating.adapter.outbound.persistence.rating_contributor import RatingContributor
from wheresmeow.rating.adapter.outbound.persistence.sql_rating_reader import SqlRatingReader
from wheresmeow.rating.application.service.rating_query_service import RatingQueryService
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
    member_service: MemberService
    authenticator: Authenticator
    game_service: GameService
    rematch_service: RematchService
    room_service: RoomService
    bot_service: BotService
    rating_query_service: RatingQueryService
    matchmaking_service: MatchmakingService
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
    bot_scheduler: Scheduler | None = None,
    match_repeater: Repeater | None = None,
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

    players = SqlPlayerStore(database, clock)
    guest_tokens = SignedTokenIssuer(config.secret_key)
    access_tokens = JwtAccessTokenIssuer(config.secret_key, clock)
    guest_service = GuestService(players, guest_tokens)
    member_service = MemberService(
        players,
        SqlAccountStore(database, clock),
        Argon2PasswordHasher(),
        access_tokens,
        SqlRefreshTokenStore(database),
        clock,
    )
    authenticator = Authenticator(players, guest_tokens, access_tokens)

    timer = turn_timer or BackgroundTurnTimer(socketio, clock)  # 턴 마감과 재대결 마감이 함께 쓴다
    game_options = {"first_seat_chooser": first_seat_chooser} if first_seat_chooser else {}
    bot_driver = BotTurnDriver(bot_scheduler or socketio_scheduler(socketio))
    game_service = GameService(
        InMemoryGameStore(),
        CompositeGameEventPublisher([SocketIOGameEventPublisher(socketio), bot_driver]),
        timer,
        layout_generator,
        clock,
        recorder=SqlGameResultRecorder(database, clock, contributors=[BotRecordContributor(), RatingContributor(clock)]),
        **game_options,
    )

    bot_driver.attach(get_game=game_service, reveal=game_service)
    rematch_service = RematchService(
        game_service, SocketIORematchNotifier(socketio), timer, clock
    )
    bot_service = BotService(
        AccountHumanDirectory(guest_service), BotGameStarterAdapter(game_service), SqlBotRecordReader(database)
    )

    rating_query_service = RatingQueryService(
        SqlRatingReader(database), RatingPlayerDirectory(guest_service), BotRecordSourceAdapter(bot_service.bot_records)
    )

    matchmaking_service = MatchmakingService(
        MatchPlayerDirectory(guest_service),
        RatingLookupAdapter(rating_query_service.current_rating),
        MatchGameStarterAdapter(game_service, game_service),
        SocketIOMatchNotifier(socketio),
        clock,
    )
    (match_repeater or socketio_repeater(socketio))(matchmaking_service.tick)  # 1초마다 짝짓기(스펙 4.3)

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
        member_service=member_service,
        authenticator=authenticator,
        game_service=game_service,
        rematch_service=rematch_service,
        room_service=room_service,
        bot_service=bot_service,
        rating_query_service=rating_query_service,
        matchmaking_service=matchmaking_service,
        http_identity=HttpIdentity(authenticator),
        socket_sessions=SocketSessions(),
    )
