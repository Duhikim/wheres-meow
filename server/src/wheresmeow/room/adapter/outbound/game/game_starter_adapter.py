from wheresmeow.game.application.port.inbound import GamePlayer, StartGameUseCase
from wheresmeow.game.domain.game import GameMode
from wheresmeow.game.domain.skins import SkinPreference
from wheresmeow.room.application.port.outbound import PlayerProfile


class GameStarterAdapter:
    """room 의 GameStarter 포트를 game 의 StartGame 유스케이스로 구현한다."""

    def __init__(self, start_game: StartGameUseCase) -> None:
        self._start_game = start_game

    def start_invite_game(self, host: PlayerProfile, guest: PlayerProfile) -> str:
        game = self._start_game.start_game(GameMode.INVITE, self._to_player(host), self._to_player(guest))
        return game.id

    @staticmethod
    def _to_player(profile: PlayerProfile) -> GamePlayer:
        return GamePlayer(profile.player_id, profile.nickname, SkinPreference(profile.skin_1p, profile.skin_2p))
