from dataclasses import dataclass
from typing import Protocol

from wheresmeow.account.domain.player import Player


class PlayerStore(Protocol):
    def save(self, player: Player) -> None: ...

    def get(self, player_id: str) -> Player | None: ...


class TokenIssuer(Protocol):
    def issue(self, player_id: str) -> str: ...

    def verify(self, token: str) -> str:
        """player_id 를 돌려준다. 위조·만료면 Unauthorized."""
        ...


@dataclass(frozen=True)
class Credential:
    player_id: str
    password_hash: str | None


class AccountStore(Protocol):
    """회원 계정. 플레이어 행과 계정 행을 한 트랜잭션으로 만든다."""

    def create_member(self, player: Player, username: str | None, password_hash: str | None) -> None: ...

    def create_oauth_member(self, player: Player, provider: str, provider_user_id: str) -> None: ...

    def find_credential(self, username: str) -> Credential | None: ...

    def username_taken(self, username: str) -> bool: ...

    def member_nickname_taken(self, nickname: str, except_player_id: str | None = None) -> bool: ...

    def find_player_by_oauth(self, provider: str, provider_user_id: str) -> str | None: ...


class PasswordHasher(Protocol):
    def hash(self, password: str) -> str: ...

    def verify(self, password_hash: str, password: str) -> bool: ...


class AccessTokenIssuer(Protocol):
    def issue(self, player_id: str) -> str: ...

    def verify(self, token: str) -> str:
        """player_id 를 돌려준다. 위조·만료면 Unauthorized."""
        ...


@dataclass(frozen=True)
class RefreshRecord:
    token_hash: str
    player_id: str
    expires_at_ms: int
    revoked_at_ms: int | None = None


class RefreshTokenStore(Protocol):
    def save(self, record: RefreshRecord) -> None: ...

    def find(self, token_hash: str) -> RefreshRecord | None: ...

    def revoke(self, token_hash: str, now_ms: int) -> bool:
        """아직 폐기되지 않았을 때만 폐기하고 True, 이미 폐기됐으면 False. 원자적이어야 한다."""
        ...

    def revoke_all(self, player_id: str, now_ms: int) -> None: ...
