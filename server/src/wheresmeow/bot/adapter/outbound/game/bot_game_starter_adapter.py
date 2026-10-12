from wheresmeow.bot.application.port.outbound import HumanProfile
from wheresmeow.bot.domain.solver import Difficulty
from wheresmeow.game.application.port.inbound import GamePlayer, StartGameUseCase
from wheresmeow.game.domain.game import GameMode
from wheresmeow.game.domain.skins import SkinPreference


class BotGameStarterAdapter:
    """bot 의 BotGameStarter 포트를 game 의 StartGame 유스케이스로 구현한다."""

    def __init__(self, start_game: StartGameUseCase) -> None:
        self._start_game = start_game

    def start_bot_game(self, human: HumanProfile, difficulty: Difficulty, bot_nickname: str) -> str:
        player = GamePlayer(human.player_id, human.nickname, SkinPreference(human.skin_1p, human.skin_2p))
        # 봇의 1P 를 사람의 2P 로 두면 스킨 배정 규칙상 사람은 1P, 봇은 사람의 2P 가 된다(스펙 4.1)
        bot = GamePlayer(
            f"bot:{difficulty.value}", bot_nickname, SkinPreference(human.skin_2p, human.skin_1p), is_bot=True
        )
        return self._start_game.start_game(GameMode.BOT, player, bot, bot_difficulty=difficulty.value).id
