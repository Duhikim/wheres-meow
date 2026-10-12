from wheresmeow.account.application.port.inbound import GetPlayerUseCase
from wheresmeow.bot.application.port.outbound import HumanProfile


class AccountHumanDirectory:
    """bot 의 HumanDirectory 포트를 account 의 GetPlayer 유스케이스로 구현한다."""

    def __init__(self, get_player: GetPlayerUseCase) -> None:
        self._get_player = get_player

    def profile(self, player_id: str) -> HumanProfile:
        player = self._get_player.get_player(player_id)
        return HumanProfile(player.id, player.nickname, player.skin_1p, player.skin_2p)
