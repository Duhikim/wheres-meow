import threading

from wheresmeow.account.domain.player import Player


class InMemoryPlayerStore:
    def __init__(self) -> None:
        self._players: dict[str, Player] = {}
        self._guard = threading.Lock()

    def save(self, player: Player) -> None:
        with self._guard:
            self._players[player.id] = player

    def get(self, player_id: str) -> Player | None:
        with self._guard:
            return self._players.get(player_id)
