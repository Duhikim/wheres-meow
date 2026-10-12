import logging
import threading

from wheresmeow.matchmaking.application.port.outbound import (
    MatchGameStarter,
    MatchNotifier,
    MatchPlayer,
    PlayerDirectory,
    RatingLookup,
)
from wheresmeow.matchmaking.domain.errors import AlreadyInGame, AlreadyQueued
from wheresmeow.matchmaking.domain.queue import Pair, Ticket, find_pairs, rating_window
from wheresmeow.shared.clock import Clock

logger = logging.getLogger(__name__)


class MatchmakingService:
    """JoinMatch·LeaveMatch 유스케이스와 1초마다 부르는 짝짓기(tick).

    대기열 전체를 잠금 하나로 보호한다. 짝지은 두 사람은 잠금 안에서 대기열에서 빼므로
    같은 사람이 두 대국에 배정되지 않는다. 대국 시작은 잠금 밖에서 한다.
    """

    def __init__(
        self,
        players: PlayerDirectory,
        ratings: RatingLookup,
        starter: MatchGameStarter,
        notifier: MatchNotifier,
        clock: Clock,
    ) -> None:
        self._players = players
        self._ratings = ratings
        self._starter = starter
        self._notifier = notifier
        self._clock = clock
        self._waiting: dict[str, tuple[Ticket, MatchPlayer]] = {}
        self._lock = threading.Lock()

    def join_match(self, player_id: str) -> None:
        if self._starter.is_in_game(player_id):
            raise AlreadyInGame(f"이미 진행 중인 대국이 있습니다: {player_id}")
        player = self._players.profile(player_id)
        ticket = Ticket(player_id, self._ratings.rating_of(player_id), self._clock.now_ms())
        with self._lock:
            if player_id in self._waiting:
                raise AlreadyQueued(f"이미 대기열에 있습니다: {player_id}")
            self._waiting[player_id] = (ticket, player)
        self._notifier.waiting_started(player_id, ticket.joined_at_ms, rating_window(ticket, ticket.joined_at_ms))

    def leave_match(self, player_id: str) -> None:
        with self._lock:
            self._waiting.pop(player_id, None)

    def is_queued(self, player_id: str) -> bool:
        with self._lock:
            return player_id in self._waiting

    def waiting_since(self, player_id: str) -> int | None:
        with self._lock:
            entry = self._waiting.get(player_id)
            return entry[0].joined_at_ms if entry else None

    def tick(self) -> None:
        with self._lock:
            pairs = find_pairs([ticket for ticket, _ in self._waiting.values()], self._clock.now_ms())
            matched = [(pair, self._waiting.pop(pair.first.player_id), self._waiting.pop(pair.second.player_id))
                       for pair in pairs]
        for pair, (_, first), (_, second) in matched:
            try:
                self._starter.start_match(first, second)
            except Exception:
                logger.exception("매칭 대국 시작 실패 first=%s second=%s", first.player_id, second.player_id)
                self._requeue(pair, first, second)

    def _requeue(self, pair: Pair, first: MatchPlayer, second: MatchPlayer) -> None:
        """대국에 들어가지 않은 사람은 원래 대기 시각 그대로 되돌려 순서와 넓어진 범위를 잃지 않게 한다."""
        for ticket, player in ((pair.first, first), (pair.second, second)):
            if self._starter.is_in_game(ticket.player_id):
                continue
            with self._lock:
                self._waiting.setdefault(ticket.player_id, (ticket, player))
