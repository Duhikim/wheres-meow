from wheresmeow.account.application.port.outbound import AccessTokenIssuer, PlayerStore, TokenIssuer
from wheresmeow.account.domain.player import Player, PlayerKind
from wheresmeow.shared.errors import Unauthorized


class Authenticator:
    """회원 액세스 토큰(JWT)과 게스트 토큰을 모두 받는 인증(Authenticate·IssueToken 유스케이스).

    HTTP 와 소켓이 모두 이것 하나를 쓴다.
    """

    def __init__(self, players: PlayerStore, guest_tokens: TokenIssuer, access_tokens: AccessTokenIssuer) -> None:
        self._players = players
        self._guest_tokens = guest_tokens
        self._access_tokens = access_tokens

    def authenticate(self, token: str) -> Player:
        player_id = self._verify(token)
        player = self._players.get(player_id)
        if player is None:
            raise Unauthorized("플레이어가 존재하지 않습니다")
        return player

    def issue_token(self, player_id: str) -> str:
        """내 정보 조회 때 새로 주는 토큰. 게스트는 30일 게스트 토큰, 회원은 15분 액세스 토큰이다."""
        player = self._players.get(player_id)
        if player is None:
            raise Unauthorized("플레이어가 존재하지 않습니다")
        issuer = self._access_tokens if player.kind is PlayerKind.MEMBER else self._guest_tokens
        return issuer.issue(player.id)

    def _verify(self, token: str) -> str:
        for issuer in (self._access_tokens, self._guest_tokens):
            try:
                return issuer.verify(token)
            except Unauthorized:
                continue
        raise Unauthorized("유효하지 않은 토큰입니다")
