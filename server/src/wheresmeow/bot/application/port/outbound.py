from dataclasses import dataclass
from typing import Protocol

from wheresmeow.bot.domain.solver import Difficulty


@dataclass(frozen=True)
class HumanProfile:
    player_id: str
    nickname: str
    skin_1p: int
    skin_2p: int


class HumanDirectory(Protocol):
    def profile(self, player_id: str) -> HumanProfile: ...


class BotGameStarter(Protocol):
    def start_bot_game(self, human: HumanProfile, difficulty: Difficulty, bot_nickname: str) -> str:
        """봇 대국을 시작하고 game_id 를 돌려준다. 사람이 1P, 봇은 그 사람의 2P 스킨을 쓴다."""
        ...


class BotRecordReader(Protocol):
    def records_of(self, player_id: str) -> dict[Difficulty, tuple[int, int, int]]:
        """난이도별 (승, 패, 무). 둔 적 없는 난이도는 빠진다."""
        ...
