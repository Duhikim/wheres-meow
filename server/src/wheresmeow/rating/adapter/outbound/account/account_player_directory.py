from wheresmeow.account.application.port.inbound import GetPlayerUseCase
from wheresmeow.rating.application.port.outbound import PlayerCard


class AccountPlayerDirectory:
    """rating 의 PlayerDirectory 포트를 account 의 GetPlayer 유스케이스로 구현한다. 없으면 PLAYER_NOT_FOUND."""

    def __init__(self, get_player: GetPlayerUseCase) -> None:
        self._get_player = get_player

    def card_of(self, player_id: str) -> PlayerCard:
        player = self._get_player.get_player(player_id)
        return PlayerCard(player.id, player.nickname, player.kind.value, player.skin_1p)
