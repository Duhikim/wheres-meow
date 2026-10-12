import secrets
import threading
import uuid
from collections.abc import Callable, Sequence

from wheresmeow.game.application.port.inbound import GamePlayer
from wheresmeow.game.application.port.outbound import GameEventPublisher, GameStore, TurnTimer
from wheresmeow.game.domain.board import BOARD_SIZE, CAT_COUNT, Board, MineLayoutGenerator
from wheresmeow.game.domain.errors import AlreadyInGame, GameNotFound
from wheresmeow.game.domain.game import Game, GameEvent, GameMode, GameStatus, Seat
from wheresmeow.game.domain.skins import assign_skins
from wheresmeow.shared.clock import Clock


class GameService:
    """StartGame·RevealCell·Forfeit·GetGame 유스케이스 구현.

    대국마다 잠금 하나를 두어 reveal·timeout·forfeit 가 순서대로 적용되게 한다.
    운영(gevent)에서는 monkey patch 로 threading.Lock 이 gevent 잠금이 된다.
    이벤트 발행과 타이머 예약도 잠금 안에서 해서 version 순서가 뒤바뀌지 않게 한다.
    """

    def __init__(
        self,
        store: GameStore,
        publisher: GameEventPublisher,
        timer: TurnTimer,
        layout_generator: MineLayoutGenerator,
        clock: Clock,
        first_seat_chooser: Callable[[], int] = lambda: secrets.randbelow(2),
        id_factory: Callable[[], str] = lambda: uuid.uuid4().hex,
    ) -> None:
        self._store = store
        self._publisher = publisher
        self._timer = timer
        self._layout_generator = layout_generator
        self._clock = clock
        self._first_seat_chooser = first_seat_chooser
        self._id_factory = id_factory
        self._locks: dict[str, threading.Lock] = {}
        self._locks_guard = threading.Lock()

    def start_game(self, mode: GameMode, priority: GamePlayer, other: GamePlayer) -> Game:
        for player in (priority, other):
            if self._store.find_active_by_player(player.player_id) is not None:
                raise AlreadyInGame(f"이미 진행 중인 대국이 있습니다: {player.player_id}")
        skin_0, skin_1 = assign_skins(priority.skins, other.skins)
        board = Board(BOARD_SIZE, self._layout_generator.generate(BOARD_SIZE, CAT_COUNT))
        seats = (
            Seat(priority.player_id, priority.nickname, skin_0),
            Seat(other.player_id, other.nickname, skin_1),
        )
        game = Game(self._id_factory(), mode, board, seats, self._first_seat_chooser(), self._clock.now_ms())
        with self._lock_for(game.id):
            self._store.save(game)
            self._publisher.game_started(game)
            self._schedule_turn(game)
        return game

    def reveal(self, game_id: str, player_id: str, x: int, y: int) -> None:
        self._act(game_id, lambda game: game.reveal(player_id, x, y, self._clock.now_ms()))

    def forfeit(self, game_id: str, player_id: str) -> None:
        self._act(game_id, lambda game: game.forfeit(player_id, self._clock.now_ms()))

    def handle_timeout(self, game_id: str, turn_seq: int) -> None:
        """TurnTimer 콜백. 그 사이 대국이 사라졌으면 아무것도 하지 않는다."""
        if self._store.get(game_id) is None:
            return
        self._act(game_id, lambda game: game.timeout(turn_seq, self._clock.now_ms()))

    def get_game(self, game_id: str, player_id: str) -> Game:
        game = self._require(game_id)
        game.seat_of(player_id)  # 참가자가 아니면 NotAParticipant
        return game

    def _act(self, game_id: str, action: Callable[[Game], Sequence[GameEvent]]) -> None:
        game = self._require(game_id)
        with self._lock_for(game_id):
            events = action(game)
            if not events:
                return
            self._store.save(game)
            self._publisher.publish(game, events)
            if game.status is GameStatus.IN_PROGRESS:
                self._schedule_turn(game)
        if game.status is GameStatus.FINISHED:
            with self._locks_guard:
                self._locks.pop(game_id, None)

    def _schedule_turn(self, game: Game) -> None:
        assert game.turn_deadline_ms is not None
        self._timer.schedule(game.id, game.turn_seq, game.turn_deadline_ms, self.handle_timeout)

    def _require(self, game_id: str) -> Game:
        game = self._store.get(game_id)
        if game is None:
            raise GameNotFound(f"대국을 찾을 수 없습니다: {game_id}")
        return game

    def _lock_for(self, game_id: str) -> threading.Lock:
        with self._locks_guard:
            return self._locks.setdefault(game_id, threading.Lock())
