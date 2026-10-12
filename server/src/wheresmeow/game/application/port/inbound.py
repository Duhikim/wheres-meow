"""game 도메인이 바깥(어댑터, 다른 도메인)에 제공하는 유스케이스."""

from dataclasses import dataclass
from typing import Protocol

from wheresmeow.game.domain.game import Game, GameMode
from wheresmeow.game.domain.skins import SkinPreference


@dataclass(frozen=True)
class GamePlayer:
    player_id: str
    nickname: str
    skins: SkinPreference
    is_bot: bool = False


class StartGameUseCase(Protocol):
    def start_game(
        self, mode: GameMode, priority: GamePlayer, other: GamePlayer, bot_difficulty: str | None = None
    ) -> Game:
        """priority 가 스킨 우선권자이며 좌석 0 에 앉는다."""
        ...


class RevealCellUseCase(Protocol):
    def reveal(self, game_id: str, player_id: str, x: int, y: int) -> None: ...


class ForfeitUseCase(Protocol):
    def forfeit(self, game_id: str, player_id: str) -> None: ...


class GetGameUseCase(Protocol):
    def get_game(self, game_id: str, player_id: str) -> Game: ...


class FindCurrentGameUseCase(Protocol):
    def find_current_game(self, player_id: str) -> Game | None: ...
