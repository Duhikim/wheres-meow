"""matchmaking 의 outbound 포트를 다른 도메인의 유스케이스와 Socket.IO 로 구현한다."""

from collections.abc import Callable

from flask_socketio import SocketIO

from wheresmeow.account.application.port.inbound import GetPlayerUseCase
from wheresmeow.game.application.port.inbound import FindCurrentGameUseCase, GamePlayer, StartGameUseCase
from wheresmeow.game.domain.game import GameMode
from wheresmeow.game.domain.skins import SkinPreference
from wheresmeow.matchmaking.application.port.outbound import MatchPlayer
from wheresmeow.shared.socket_rooms import player_room


class AccountPlayerDirectory:
    def __init__(self, get_player: GetPlayerUseCase) -> None:
        self._get_player = get_player

    def profile(self, player_id: str) -> MatchPlayer:
        player = self._get_player.get_player(player_id)
        return MatchPlayer(player.id, player.nickname, player.skin_1p, player.skin_2p)


class RatingLookupAdapter:
    def __init__(self, current_rating: Callable[[str], int]) -> None:
        self._current_rating = current_rating

    def rating_of(self, player_id: str) -> int:
        return self._current_rating(player_id)


class MatchGameStarterAdapter:
    def __init__(self, start_game: StartGameUseCase, current_game: FindCurrentGameUseCase) -> None:
        self._start_game = start_game
        self._current_game = current_game

    def is_in_game(self, player_id: str) -> bool:
        return self._current_game.find_current_game(player_id) is not None

    def start_match(self, first: MatchPlayer, second: MatchPlayer) -> None:
        self._start_game.start_game(GameMode.MATCH, _game_player(first), _game_player(second))
        # game:started 는 GameEventPublisher 가 두 사람에게 보낸다


class SocketIOMatchNotifier:
    def __init__(self, socketio: SocketIO) -> None:
        self._socketio = socketio

    def waiting_started(self, player_id: str, since_ms: int, rating_range: int | None) -> None:
        self._socketio.emit("match:waiting", {"since": since_ms, "range": rating_range}, to=player_room(player_id))


def _game_player(player: MatchPlayer) -> GamePlayer:
    return GamePlayer(player.player_id, player.nickname, SkinPreference(player.skin_1p, player.skin_2p))
