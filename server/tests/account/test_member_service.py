import itertools

import pytest

from account.member_fakes import (
    FakeAccessTokens,
    FakeAccountStore,
    FakeHasher,
    FakePlayerStore,
    FakeRefreshStore,
    RacingRefreshStore,
)
from fakes import FakeClock
from wheresmeow.account.application.service.member_service import REFRESH_TTL_MS, MemberService
from wheresmeow.account.domain.member import InvalidCredentials, NicknameTaken, UsernameTaken
from wheresmeow.account.domain.player import Player, PlayerKind
from wheresmeow.shared.errors import InvalidInput, Unauthorized


@pytest.fixture
def env():
    players = FakePlayerStore()
    accounts = FakeAccountStore(players)
    refresh = FakeRefreshStore()
    clock = FakeClock(now_ms=0)
    ids = (f"m{i}" for i in itertools.count(1))
    tokens = (f"refresh-{i}" for i in itertools.count(1))
    service = MemberService(
        players,
        accounts,
        FakeHasher(),
        FakeAccessTokens(),
        refresh,
        clock,
        id_factory=lambda: next(ids),
        token_factory=lambda: next(tokens),
    )
    return service, players, refresh, clock


class TestMemberService:
    class TestSignup:
        def test_성공_회원을_만들고_액세스·리프레시_토큰을_준다(self, env):
            service, players, *_ = env

            result = service.signup("neko_01", "password1", "고양이집사")

            assert (result.player.kind, result.player.nickname) == (PlayerKind.MEMBER, "고양이집사")
            assert result.access_token == f"access:{result.player.id}"
            assert result.refresh_token == "refresh-1"
            assert players.get(result.player.id) is not None

        @pytest.mark.parametrize("username", ["abc", "a" * 21, "Neko01", "neko-01", "냥냥이1"])
        def test_실패_아이디가_4_20자_영문소문자_숫자_밑줄이_아니면_거부한다(self, env, username):
            service, *_ = env

            with pytest.raises(InvalidInput):
                service.signup(username, "password1", "고양이집사")

        def test_실패_비밀번호가_8자_미만이면_거부한다(self, env):
            service, *_ = env

            with pytest.raises(InvalidInput):
                service.signup("neko_01", "short", "고양이집사")

        def test_실패_이미_쓰는_아이디면_USERNAME_TAKEN(self, env):
            service, *_ = env
            service.signup("neko_01", "password1", "첫번째냥")

            with pytest.raises(UsernameTaken):
                service.signup("neko_01", "password2", "두번째냥")

        def test_실패_다른_회원이_쓰는_닉네임이면_NICKNAME_TAKEN(self, env):
            service, *_ = env
            service.signup("neko_01", "password1", "고양이집사")

            with pytest.raises(NicknameTaken):
                service.signup("neko_02", "password1", "고양이집사")

        def test_성공_게스트가_쓰는_닉네임은_회원이_써도_된다(self, env):
            service, players, *_ = env
            players.save(Player("g1", PlayerKind.GUEST, "고양이집사"))

            assert service.signup("neko_01", "password1", "고양이집사").player.nickname == "고양이집사"

    class TestLogin:
        def test_성공_맞는_비밀번호면_토큰을_준다(self, env):
            service, *_ = env
            member = service.signup("neko_01", "password1", "고양이집사").player

            result = service.login("neko_01", "password1")

            assert result.player.id == member.id

        @pytest.mark.parametrize(("username", "password"), [("neko_01", "wrong-pass"), ("nobody", "password1")])
        def test_실패_틀린_비밀번호와_없는_아이디는_같은_오류다(self, env, username, password):
            service, *_ = env
            service.signup("neko_01", "password1", "고양이집사")

            with pytest.raises(InvalidCredentials):
                service.login(username, password)

    class TestRefresh:
        def test_성공_새_토큰을_주고_예전_리프레시_토큰은_폐기한다(self, env):
            service, *_ = env
            first = service.signup("neko_01", "password1", "고양이집사")

            second = service.refresh(first.refresh_token)

            assert second.refresh_token != first.refresh_token
            assert second.player.id == first.player.id
            with pytest.raises(Unauthorized):
                service.refresh(first.refresh_token)

        def test_실패_폐기된_토큰을_다시_쓰면_그_회원의_토큰을_모두_폐기한다(self, env):
            service, *_ = env
            first = service.signup("neko_01", "password1", "고양이집사")
            second = service.refresh(first.refresh_token)

            with pytest.raises(Unauthorized):
                service.refresh(first.refresh_token)  # 탈취된 예전 토큰의 재사용

            with pytest.raises(Unauthorized):
                service.refresh(second.refresh_token)  # 정상 사용자 쪽 토큰도 함께 폐기됨

        def test_실패_14일이_지난_토큰이면_거부한다(self, env):
            service, _, _, clock = env
            first = service.signup("neko_01", "password1", "고양이집사")
            clock.advance(REFRESH_TTL_MS)

            with pytest.raises(Unauthorized):
                service.refresh(first.refresh_token)

        def test_실패_모르는_토큰이면_거부한다(self, env):
            service, *_ = env

            with pytest.raises(Unauthorized):
                service.refresh("forged")

        def test_실패_같은_토큰으로_동시에_두_번_오면_늦은_쪽은_재사용으로_거부한다(self):
            players = FakePlayerStore()
            store = RacingRefreshStore()
            service = MemberService(
                players, FakeAccountStore(players), FakeHasher(), FakeAccessTokens(), store, FakeClock(0)
            )
            first = service.signup("neko_01", "password1", "고양이집사")

            with pytest.raises(Unauthorized):
                service.refresh(first.refresh_token)

    class TestLogout:
        def test_성공_로그아웃한_리프레시_토큰은_다시_쓸_수_없다(self, env):
            service, *_ = env
            first = service.signup("neko_01", "password1", "고양이집사")

            service.logout(first.refresh_token)

            with pytest.raises(Unauthorized):
                service.refresh(first.refresh_token)

        def test_성공_모르는_토큰으로_로그아웃해도_오류가_없다(self, env):
            service, *_ = env

            service.logout("forged")

    class TestOAuthLogin:
        def test_성공_처음이면_회원을_만들고_닉네임_설정이_필요하다(self, env):
            service, *_ = env

            result, is_new = service.oauth_login("kakao", "k-123")

            assert is_new is True
            assert result.player.kind is PlayerKind.MEMBER
            assert result.player.needs_nickname is True

        def test_성공_두_번째부터는_같은_회원으로_로그인한다(self, env):
            service, *_ = env
            first, _ = service.oauth_login("kakao", "k-123")

            again, is_new = service.oauth_login("kakao", "k-123")

            assert (again.player.id, is_new) == (first.player.id, False)

        def test_성공_제공자가_다르면_다른_회원이다(self, env):
            service, *_ = env
            kakao, _ = service.oauth_login("kakao", "same-id")

            naver, _ = service.oauth_login("naver", "same-id")

            assert kakao.player.id != naver.player.id

    class TestChangeNickname:
        def test_성공_닉네임을_바꾸면_닉네임_설정_필요_표시가_꺼진다(self, env):
            service, *_ = env
            result, _ = service.oauth_login("google", "g-1")

            player = service.change_nickname(result.player.id, "구글냥")

            assert (player.nickname, player.needs_nickname) == ("구글냥", False)

        def test_실패_회원이_다른_회원의_닉네임으로_바꾸면_NICKNAME_TAKEN(self, env):
            service, *_ = env
            service.signup("neko_01", "password1", "고양이집사")
            other = service.signup("neko_02", "password1", "다른냥").player

            with pytest.raises(NicknameTaken):
                service.change_nickname(other.id, "고양이집사")

        def test_성공_게스트는_회원_닉네임과_같아도_바꿀_수_있다(self, env):
            service, players, *_ = env
            service.signup("neko_01", "password1", "고양이집사")
            players.save(Player("g1", PlayerKind.GUEST, "게스트냥"))

            assert service.change_nickname("g1", "고양이집사").nickname == "고양이집사"
