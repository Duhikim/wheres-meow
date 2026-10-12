import threading

from wheresmeow.game.domain.game import Game, GameStatus
from wheresmeow.shared.clock import Clock, SystemClock

# 끝난 대국을 결과 화면·재대결·game:sync 를 위해 남겨 두는 시간. 재대결 마감(30초)보다 넉넉하다.
FINISHED_RETENTION_MS = 10 * 60_000


class InMemoryGameStore:
    """단일 프로세스용. 플레이어별 진행 중 대국 색인을 두어 전체를 훑지 않고,
    끝난 대국은 보관 시간이 지나면 다음 저장 때 지운다(서버가 오래 떠 있어도 메모리가 늘지 않게).
    """

    def __init__(self, clock: Clock | None = None, retention_ms: int = FINISHED_RETENTION_MS) -> None:
        self._clock = clock or SystemClock()
        self._retention_ms = retention_ms
        self._games: dict[str, Game] = {}
        self._active_by_player: dict[str, str] = {}
        self._finished_at: dict[str, int] = {}
        self._guard = threading.Lock()

    def save(self, game: Game) -> None:
        with self._guard:
            self._games[game.id] = game
            for seat in game.seats:
                if game.status is GameStatus.IN_PROGRESS:
                    self._active_by_player[seat.player_id] = game.id
                elif self._active_by_player.get(seat.player_id) == game.id:
                    del self._active_by_player[seat.player_id]
            if game.status is GameStatus.FINISHED:
                self._finished_at.setdefault(game.id, self._clock.now_ms())
            self._prune()

    def get(self, game_id: str) -> Game | None:
        with self._guard:
            return self._games.get(game_id)

    def find_active_by_player(self, player_id: str) -> Game | None:
        with self._guard:
            game_id = self._active_by_player.get(player_id)
            return self._games.get(game_id) if game_id else None

    def forget(self, game_id: str) -> None:
        """끝난 대국을 지금 지운다(보관 시간 경과와 같은 효과, 테스트용)."""
        with self._guard:
            self._remove(game_id)

    def _prune(self) -> None:
        cutoff = self._clock.now_ms() - self._retention_ms
        for game_id in [g for g, at in self._finished_at.items() if at <= cutoff]:
            self._remove(game_id)

    def _remove(self, game_id: str) -> None:
        self._games.pop(game_id, None)
        self._finished_at.pop(game_id, None)
