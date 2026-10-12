import threading

from wheresmeow.game.domain.game import Game, GameStatus


class InMemoryGameStore:
    """단일 프로세스용. 끝난 대국도 결과 화면을 위해 남겨 둔다."""

    def __init__(self) -> None:
        self._games: dict[str, Game] = {}
        self._guard = threading.Lock()

    def save(self, game: Game) -> None:
        with self._guard:
            self._games[game.id] = game

    def get(self, game_id: str) -> Game | None:
        with self._guard:
            return self._games.get(game_id)

    def find_active_by_player(self, player_id: str) -> Game | None:
        with self._guard:
            return next(
                (
                    g
                    for g in self._games.values()
                    if g.status is GameStatus.IN_PROGRESS and g.is_participant(player_id)
                ),
                None,
            )
