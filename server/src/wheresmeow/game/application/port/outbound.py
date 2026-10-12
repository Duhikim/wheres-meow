"""game 도메인이 바깥에 요구하는 기능."""

from collections.abc import Callable, Sequence
from typing import Protocol

from wheresmeow.game.domain.game import Game, GameEvent


class GameStore(Protocol):
    def save(self, game: Game) -> None: ...

    def get(self, game_id: str) -> Game | None: ...

    def find_active_by_player(self, player_id: str) -> Game | None: ...


class GameEventPublisher(Protocol):
    def game_started(self, game: Game) -> None: ...

    def publish(self, game: Game, events: Sequence[GameEvent]) -> None: ...


class TurnTimer(Protocol):
    def schedule(
        self,
        game_id: str,
        turn_seq: int,
        deadline_ms: int,
        on_expire: Callable[[str, int], None],
    ) -> None:
        """deadline_ms 가 지나면 on_expire(game_id, turn_seq) 를 호출한다."""
        ...
