import uuid
from collections.abc import Callable

from wheresmeow.account.application.port.inbound import GuestCredentials
from wheresmeow.account.application.port.outbound import PlayerStore, TokenIssuer
from wheresmeow.account.domain.player import Player, PlayerKind, normalize_nickname
from wheresmeow.shared.errors import DomainError, Unauthorized


class PlayerNotFound(DomainError):
    code = "PLAYER_NOT_FOUND"


class GuestService:
    """CreateGuest·Authenticate·GetPlayer 유스케이스 구현."""

    def __init__(
        self,
        store: PlayerStore,
        tokens: TokenIssuer,
        id_factory: Callable[[], str] = lambda: uuid.uuid4().hex,
    ) -> None:
        self._store = store
        self._tokens = tokens
        self._id_factory = id_factory

    def create_guest(self, nickname: str) -> GuestCredentials:
        player = Player(self._id_factory(), PlayerKind.GUEST, normalize_nickname(nickname))
        self._store.save(player)
        return GuestCredentials(player, self._tokens.issue(player.id))

    def authenticate(self, token: str) -> Player:
        player = self._store.get(self._tokens.verify(token))
        if player is None:
            raise Unauthorized("플레이어가 존재하지 않습니다")
        return player

    def get_player(self, player_id: str) -> Player:
        player = self._store.get(player_id)
        if player is None:
            raise PlayerNotFound(f"플레이어를 찾을 수 없습니다: {player_id}")
        return player
