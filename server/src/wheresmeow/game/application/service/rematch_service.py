import logging
import threading

from wheresmeow.game.application.port.outbound import RematchNotifier, TurnTimer
from wheresmeow.game.application.service.game_service import GameService
from wheresmeow.game.domain.game import Game, GameStatus
from wheresmeow.game.domain.rematch import Rematch
from wheresmeow.shared.clock import Clock
from wheresmeow.shared.errors import DomainError, InvalidInput

logger = logging.getLogger(__name__)


class RematchService:
    """RequestRematch·DeclineRematch·LeaveResult 유스케이스(스펙 4.1).

    끝난 대국마다 Rematch 하나를 두고, 전체를 잠금 하나로 보호해 동시에 수락해도 새 대국은 하나만 만든다.
    30초 마감은 턴 타이머 포트로 예약한다(대국마다 한 번이라 turn_seq 자리에는 0 을 넣는다).
    """

    def __init__(self, games: GameService, notifier: RematchNotifier, timer: TurnTimer, clock: Clock) -> None:
        self._games = games
        self._notifier = notifier
        self._timer = timer
        self._clock = clock
        self._rematches: dict[str, Rematch] = {}
        self._lock = threading.Lock()

    def prune(self) -> None:
        """저장소에서 지워진 대국의 협상 상태를 버린다. 그 대국으로는 어차피 GAME_NOT_FOUND 가 난다."""
        with self._lock:
            for game_id in [g for g in self._rematches if not self._games.is_known(g)]:
                del self._rematches[game_id]

    def tracked_game_ids(self) -> list[str]:
        with self._lock:
            return list(self._rematches)

    def request_rematch(self, game_id: str, player_id: str) -> None:
        self.prune()
        game = self._finished_game(game_id, player_id)
        with self._lock:
            rematch = self._rematch_for(game)
            first_request = rematch.deadline_ms is None
            start = rematch.request(player_id, self._clock.now_ms())
            if start:
                self._start(game, rematch)
                return
            self._notifier.rematch_requested(game_id, rematch.opponent_of(player_id))
            if first_request:
                assert rematch.deadline_ms is not None
                self._timer.schedule(game_id, 0, rematch.deadline_ms, self.handle_expiry)

    def decline_rematch(self, game_id: str, player_id: str) -> None:
        self.prune()
        game = self._finished_game(game_id, player_id)
        with self._lock:
            notify = self._rematch_for(game).decline(player_id)
        if notify:
            self._notifier.rematch_cancelled(game_id, notify, "DECLINED")

    def leave_result(self, game_id: str, player_id: str) -> None:
        self.prune()
        game = self._finished_game(game_id, player_id)
        with self._lock:
            notify = self._rematch_for(game).leave(player_id)
        if notify:
            self._notifier.rematch_cancelled(game_id, notify, "LEFT")

    def handle_expiry(self, game_id: str, _seq: int) -> None:
        with self._lock:
            rematch = self._rematches.get(game_id)
            notify = rematch.expire(self._clock.now_ms()) if rematch else []
        if notify:
            self._notifier.rematch_cancelled(game_id, notify, "EXPIRED")

    def _start(self, game: Game, rematch: Rematch) -> None:
        try:
            self._games.start_rematch(game)  # game:started 는 GameEventPublisher 가 보낸다
        except DomainError as error:
            logger.info("재대결 대국을 만들지 못했습니다 game_id=%s code=%s", game.id, error.code)
            self._notifier.rematch_cancelled(game.id, [p for p in rematch.fail() if p != rematch.bot_player_id],
                                             "UNAVAILABLE")

    def _finished_game(self, game_id: str, player_id: str) -> Game:
        game = self._games.get_game(game_id, player_id)  # 없으면 GAME_NOT_FOUND, 참가자가 아니면 NOT_A_PARTICIPANT
        if game.status is not GameStatus.FINISHED:
            raise InvalidInput(f"아직 끝나지 않은 대국입니다: {game_id}")
        return game

    def _rematch_for(self, game: Game) -> Rematch:
        rematch = self._rematches.get(game.id)
        if rematch is None:
            bot = next((s.player_id for s in game.seats if s.is_bot), None)
            rematch = Rematch(game.id, (game.seats[0].player_id, game.seats[1].player_id), bot_player_id=bot)
            self._rematches[game.id] = rematch
        return rematch
