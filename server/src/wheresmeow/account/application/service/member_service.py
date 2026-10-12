import hashlib
import secrets
import uuid
from collections.abc import Callable
from dataclasses import dataclass

from wheresmeow.account.application.port.outbound import (
    AccessTokenIssuer,
    AccountStore,
    PasswordHasher,
    PlayerStore,
    RefreshRecord,
    RefreshTokenStore,
)
from wheresmeow.account.application.service.guest_service import PlayerNotFound
from wheresmeow.account.domain.member import (
    InvalidCredentials,
    NicknameTaken,
    UsernameTaken,
    validate_password,
    validate_username,
)
from wheresmeow.account.domain.player import Player, PlayerKind, normalize_nickname
from wheresmeow.shared.clock import Clock
from wheresmeow.shared.errors import Unauthorized

REFRESH_TTL_MS = 14 * 24 * 60 * 60 * 1000
# 없는 아이디로 로그인할 때도 해시 검증 시간을 똑같이 써서, 응답 시간으로 아이디 존재를 알 수 없게 한다
_DUMMY_PASSWORD = "dummy-password-for-timing"


@dataclass(frozen=True)
class AuthResult:
    player: Player
    access_token: str
    refresh_token: str


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class MemberService:
    """Signup·Login·Refresh·Logout·OAuthLogin·ChangeNickname 유스케이스 구현(스펙 4.4)."""

    def __init__(
        self,
        players: PlayerStore,
        accounts: AccountStore,
        hasher: PasswordHasher,
        access_tokens: AccessTokenIssuer,
        refresh_tokens: RefreshTokenStore,
        clock: Clock,
        id_factory: Callable[[], str] = lambda: uuid.uuid4().hex,
        token_factory: Callable[[], str] = lambda: secrets.token_urlsafe(32),
    ) -> None:
        self._players = players
        self._accounts = accounts
        self._hasher = hasher
        self._access = access_tokens
        self._refresh = refresh_tokens
        self._clock = clock
        self._id_factory = id_factory
        self._token_factory = token_factory
        self._dummy_hash = hasher.hash(_DUMMY_PASSWORD)

    def signup(self, username: str, password: str, nickname: str) -> AuthResult:
        username = validate_username(username)
        validate_password(password)
        nickname = normalize_nickname(nickname)
        if self._accounts.username_taken(username):
            raise UsernameTaken("이미 쓰는 아이디입니다")
        if self._accounts.member_nickname_taken(nickname):
            raise NicknameTaken("이미 쓰는 닉네임입니다")
        player = Player(self._id_factory(), PlayerKind.MEMBER, nickname)
        self._accounts.create_member(player, username, self._hasher.hash(password))
        return self._issue(player)

    def login(self, username: str, password: str) -> AuthResult:
        credential = self._accounts.find_credential(username)
        if credential is None or credential.password_hash is None:
            self._hasher.verify(self._dummy_hash, password)
            raise InvalidCredentials("아이디 또는 비밀번호가 맞지 않습니다")
        if not self._hasher.verify(credential.password_hash, password):
            raise InvalidCredentials("아이디 또는 비밀번호가 맞지 않습니다")
        return self._issue(self._require_player(credential.player_id))

    def refresh(self, refresh_token: str) -> AuthResult:
        now = self._clock.now_ms()
        record = self._refresh.find(hash_refresh_token(refresh_token))
        if record is None:
            raise Unauthorized("유효하지 않은 리프레시 토큰입니다")
        if now >= record.expires_at_ms:
            raise Unauthorized("만료된 리프레시 토큰입니다")
        # 조회와 폐기 사이에 같은 토큰을 쓴 요청이 있을 수 있으므로, 폐기에 성공한 한 요청만 새 토큰을 받는다
        if record.revoked_at_ms is not None or not self._refresh.revoke(record.token_hash, now):
            # 이미 바꿔 준 토큰이 다시 왔다 = 탈취 가능성. 그 회원의 토큰을 모두 끊는다.
            self._refresh.revoke_all(record.player_id, now)
            raise Unauthorized("이미 사용한 리프레시 토큰입니다")
        return self._issue(self._require_player(record.player_id))

    def logout(self, refresh_token: str) -> None:
        record = self._refresh.find(hash_refresh_token(refresh_token))
        if record is not None and record.revoked_at_ms is None:
            self._refresh.revoke(record.token_hash, self._clock.now_ms())

    def oauth_login(self, provider: str, provider_user_id: str) -> tuple[AuthResult, bool]:
        """(결과, 새로 가입했는지). 처음이면 임시 닉네임으로 만들고 닉네임 설정을 요구한다."""
        player_id = self._accounts.find_player_by_oauth(provider, provider_user_id)
        if player_id is not None:
            return self._issue(self._require_player(player_id)), False
        player = Player(self._id_factory(), PlayerKind.MEMBER, self._temporary_nickname(), needs_nickname=True)
        self._accounts.create_oauth_member(player, provider, provider_user_id)
        return self._issue(player), True

    def change_nickname(self, player_id: str, nickname: str) -> Player:
        player = self._require_player(player_id)
        nickname = normalize_nickname(nickname)
        if player.kind is PlayerKind.MEMBER and self._accounts.member_nickname_taken(nickname, except_player_id=player.id):
            raise NicknameTaken("이미 쓰는 닉네임입니다")
        player.rename(nickname)
        self._players.save(player)
        return player

    # ---- 내부 ----

    def _issue(self, player: Player) -> AuthResult:
        refresh_token = self._token_factory()
        expires = self._clock.now_ms() + REFRESH_TTL_MS
        self._refresh.save(RefreshRecord(hash_refresh_token(refresh_token), player.id, expires))
        return AuthResult(player, self._access.issue(player.id), refresh_token)

    def _require_player(self, player_id: str) -> Player:
        player = self._players.get(player_id)
        if player is None:
            raise PlayerNotFound(f"플레이어를 찾을 수 없습니다: {player_id}")
        return player

    def _temporary_nickname(self) -> str:
        for _ in range(20):
            candidate = f"냥{secrets.randbelow(1_000_000):06d}"
            if not self._accounts.member_nickname_taken(candidate):
                return candidate
        raise RuntimeError("임시 닉네임을 만들지 못했습니다")
