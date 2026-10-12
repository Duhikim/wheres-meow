"""회원 서비스 테스트용 가짜 어댑터."""

from wheresmeow.account.application.port.outbound import Credential, RefreshRecord
from wheresmeow.account.domain.player import Player, PlayerKind
from wheresmeow.shared.errors import Unauthorized


class FakePlayerStore:
    def __init__(self) -> None:
        self.players: dict[str, Player] = {}

    def save(self, player: Player) -> None:
        self.players[player.id] = player

    def get(self, player_id: str) -> Player | None:
        return self.players.get(player_id)


class FakeAccountStore:
    def __init__(self, players: FakePlayerStore) -> None:
        self.players = players
        self.credentials: dict[str, Credential] = {}
        self.oauth: dict[tuple[str, str], str] = {}

    def create_member(self, player: Player, username: str | None, password_hash: str | None) -> None:
        self.players.save(player)
        if username is not None:
            self.credentials[username] = Credential(player.id, password_hash)

    def create_oauth_member(self, player: Player, provider: str, provider_user_id: str) -> None:
        self.players.save(player)
        self.oauth[(provider, provider_user_id)] = player.id

    def find_credential(self, username: str) -> Credential | None:
        return self.credentials.get(username)

    def username_taken(self, username: str) -> bool:
        return username in self.credentials

    def member_nickname_taken(self, nickname: str, except_player_id: str | None = None) -> bool:
        return any(
            p.kind is PlayerKind.MEMBER and p.nickname == nickname and p.id != except_player_id
            for p in self.players.players.values()
        )

    def find_player_by_oauth(self, provider: str, provider_user_id: str) -> str | None:
        return self.oauth.get((provider, provider_user_id))


class FakeHasher:
    def hash(self, password: str) -> str:
        return f"hashed:{password}"

    def verify(self, password_hash: str, password: str) -> bool:
        return password_hash == f"hashed:{password}"


class FakeAccessTokens:
    def issue(self, player_id: str) -> str:
        return f"access:{player_id}"

    def verify(self, token: str) -> str:
        if not token.startswith("access:"):
            raise Unauthorized()
        return token.removeprefix("access:")


class FakeRefreshStore:
    def __init__(self) -> None:
        self.records: dict[str, RefreshRecord] = {}

    def save(self, record: RefreshRecord) -> None:
        self.records[record.token_hash] = record

    def find(self, token_hash: str) -> RefreshRecord | None:
        return self.records.get(token_hash)

    def revoke(self, token_hash: str, now_ms: int) -> bool:
        record = self.records[token_hash]
        if record.revoked_at_ms is not None:
            return False
        self.records[token_hash] = RefreshRecord(record.token_hash, record.player_id, record.expires_at_ms, now_ms)
        return True

    def revoke_all(self, player_id: str, now_ms: int) -> None:
        for token_hash, record in list(self.records.items()):
            if record.player_id == player_id and record.revoked_at_ms is None:
                self.revoke(token_hash, now_ms)


class RacingRefreshStore(FakeRefreshStore):
    """조회와 폐기 사이에 다른 요청이 같은 토큰을 먼저 폐기한 상황을 흉내 낸다."""

    def find(self, token_hash: str):
        record = super().find(token_hash)
        if record is not None and record.revoked_at_ms is None:
            super().revoke(token_hash, now_ms=0)  # 다른 요청이 먼저 썼다
            return record  # 이 요청은 폐기 전 상태를 읽었다
        return record
