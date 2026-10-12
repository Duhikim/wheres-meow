import pytest
from sqlalchemy.exc import IntegrityError

from fakes import FakeClock
from persistence_support import migrated_database
from wheresmeow.account.adapter.outbound.persistence.sql_account_store import SqlAccountStore
from wheresmeow.account.adapter.outbound.persistence.sql_player_store import SqlPlayerStore
from wheresmeow.account.adapter.outbound.persistence.sql_refresh_token_store import SqlRefreshTokenStore
from wheresmeow.account.adapter.outbound.token.argon2_password_hasher import Argon2PasswordHasher
from wheresmeow.account.adapter.outbound.token.jwt_access_token_issuer import ACCESS_TTL_MS, JwtAccessTokenIssuer
from wheresmeow.account.adapter.outbound.token.signed_token_issuer import SignedTokenIssuer
from wheresmeow.account.application.port.outbound import RefreshRecord
from wheresmeow.account.domain.member import NicknameTaken, UsernameTaken
from wheresmeow.account.domain.player import Player, PlayerKind
from wheresmeow.shared.errors import Unauthorized


@pytest.fixture
def stores():
    database = migrated_database()
    clock = FakeClock()
    return SqlAccountStore(database, clock), SqlPlayerStore(database, clock), database


class TestSqlAccountStore:
    class TestCreateMember:
        def test_성공_플레이어와_계정을_함께_만들고_아이디로_찾는다(self, stores):
            accounts, players, _ = stores

            accounts.create_member(Player("m1", PlayerKind.MEMBER, "고양이집사"), "neko_01", "hash")

            assert accounts.find_credential("neko_01").player_id == "m1"
            assert accounts.username_taken("neko_01")
            assert players.get("m1").kind is PlayerKind.MEMBER

        def test_실패_같은_아이디로_두_번_만들면_USERNAME_TAKEN(self, stores):
            accounts, *_ = stores
            accounts.create_member(Player("m1", PlayerKind.MEMBER, "첫째냥"), "neko_01", "hash")

            with pytest.raises(UsernameTaken):
                accounts.create_member(Player("m2", PlayerKind.MEMBER, "둘째냥"), "neko_01", "hash")

        def test_실패_DB가_회원_닉네임_중복을_직접_막는다(self, stores):
            accounts, *_ = stores
            accounts.create_member(Player("m1", PlayerKind.MEMBER, "고양이집사"), "neko_01", "hash")

            with pytest.raises(NicknameTaken):
                accounts.create_member(Player("m2", PlayerKind.MEMBER, "고양이집사"), "neko_02", "hash")

        def test_성공_게스트와_회원은_같은_닉네임을_쓸_수_있다(self, stores):
            accounts, players, _ = stores
            players.save(Player("g1", PlayerKind.GUEST, "고양이집사"))
            players.save(Player("g2", PlayerKind.GUEST, "고양이집사"))

            accounts.create_member(Player("m1", PlayerKind.MEMBER, "고양이집사"), "neko_01", "hash")

            assert accounts.member_nickname_taken("고양이집사")
            assert not accounts.member_nickname_taken("고양이집사", except_player_id="m1")

        def test_실패_회원_닉네임을_다른_회원과_같게_바꾸면_DB가_막는다(self, stores):
            accounts, players, _ = stores
            accounts.create_member(Player("m1", PlayerKind.MEMBER, "첫째냥"), "neko_01", "hash")
            accounts.create_member(Player("m2", PlayerKind.MEMBER, "둘째냥"), "neko_02", "hash")

            with pytest.raises(IntegrityError):
                players.save(Player("m2", PlayerKind.MEMBER, "첫째냥"))

    class TestOAuth:
        def test_성공_소셜_계정으로_만든_회원을_제공자와_ID로_찾는다(self, stores):
            accounts, players, _ = stores

            accounts.create_oauth_member(Player("m1", PlayerKind.MEMBER, "냥000001", needs_nickname=True), "kakao", "k-1")

            assert accounts.find_player_by_oauth("kakao", "k-1") == "m1"
            assert accounts.find_player_by_oauth("naver", "k-1") is None
            assert players.get("m1").needs_nickname is True
            assert accounts.find_credential("anything") is None


class TestSqlRefreshTokenStore:
    class TestLifecycle:
        def test_성공_저장_조회_폐기_전체폐기(self):
            store = SqlRefreshTokenStore(migrated_database())
            store.save(RefreshRecord("h1", "m1", 1000))
            store.save(RefreshRecord("h2", "m1", 1000))

            assert store.revoke("h1", now_ms=10) is True
            assert store.revoke("h1", now_ms=11) is False  # 이미 폐기됨: 먼저 쓴 쪽만 성공한다
            assert store.find("h1").revoked_at_ms == 10
            assert store.find("h2").revoked_at_ms is None

            store.revoke_all("m1", now_ms=20)
            assert store.find("h2").revoked_at_ms == 20
            assert store.find("h1").revoked_at_ms == 10  # 이미 폐기된 것은 그대로
            assert store.find("nope") is None


class TestArgon2PasswordHasher:
    class TestVerify:
        def test_성공_같은_비밀번호면_참_다르면_거짓(self):
            hasher = Argon2PasswordHasher()
            hashed = hasher.hash("password1")

            assert hashed.startswith("$argon2id$")
            assert hasher.verify(hashed, "password1")
            assert not hasher.verify(hashed, "password2")

        def test_성공_망가진_해시는_거짓이다(self):
            assert not Argon2PasswordHasher().verify("not-a-hash", "password1")


class TestJwtAccessTokenIssuer:
    class TestVerify:
        def test_성공_발급한_토큰에서_player_id를_꺼낸다(self):
            issuer = JwtAccessTokenIssuer("secret", FakeClock(now_ms=1_000_000))

            assert issuer.verify(issuer.issue("m1")) == "m1"

        def test_실패_15분이_지나면_거부한다(self):
            clock = FakeClock(now_ms=1_000_000)
            issuer = JwtAccessTokenIssuer("secret", clock)
            token = issuer.issue("m1")
            clock.advance(ACCESS_TTL_MS)

            with pytest.raises(Unauthorized):
                issuer.verify(token)

        def test_실패_다른_키로_서명한_토큰이면_거부한다(self):
            token = JwtAccessTokenIssuer("other", FakeClock()).issue("m1")

            with pytest.raises(Unauthorized):
                JwtAccessTokenIssuer("secret", FakeClock()).verify(token)

        def test_실패_게스트_토큰은_액세스_토큰으로_받지_않는다(self):
            guest_token = SignedTokenIssuer("secret").issue("g1")

            with pytest.raises(Unauthorized):
                JwtAccessTokenIssuer("secret", FakeClock()).verify(guest_token)
