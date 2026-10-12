import pytest

from wheresmeow.account.adapter.outbound.memory.in_memory_player_store import InMemoryPlayerStore
from wheresmeow.account.adapter.outbound.token.signed_token_issuer import SignedTokenIssuer
from wheresmeow.account.application.service.guest_service import GuestService, PlayerNotFound
from wheresmeow.account.domain.player import PlayerKind, normalize_nickname
from wheresmeow.shared.errors import InvalidInput, Unauthorized


class TestNormalizeNickname:
    class TestNormalize:
        def test_성공_앞뒤_공백을_제거한다(self):
            assert normalize_nickname("  냥냥  ") == "냥냥"

        @pytest.mark.parametrize("raw", ["냥", "   냥  ", "가" * 13, ""])
        def test_실패_2자_미만이거나_12자_초과면_거부한다(self, raw):
            with pytest.raises(InvalidInput):
                normalize_nickname(raw)


class TestSignedTokenIssuer:
    class TestVerify:
        def test_성공_발급한_토큰에서_player_id를_꺼낸다(self):
            issuer = SignedTokenIssuer("secret")

            assert issuer.verify(issuer.issue("p1")) == "p1"

        def test_실패_다른_키로_서명한_토큰이면_거부한다(self):
            token = SignedTokenIssuer("other").issue("p1")

            with pytest.raises(Unauthorized):
                SignedTokenIssuer("secret").verify(token)

        def test_실패_만료된_토큰이면_거부한다(self):
            issuer = SignedTokenIssuer("secret", max_age_seconds=-1)

            with pytest.raises(Unauthorized):
                issuer.verify(issuer.issue("p1"))

    class TestInit:
        def test_실패_서명_키가_비어_있으면_거부한다(self):
            with pytest.raises(ValueError):
                SignedTokenIssuer("")


class TestGuestService:
    @pytest.fixture
    def service(self):
        return GuestService(InMemoryPlayerStore(), SignedTokenIssuer("secret"), id_factory=lambda: "p1")

    class TestCreateGuest:
        def test_성공_게스트를_만들고_기본_스킨과_토큰을_준다(self, service):
            credentials = service.create_guest(" 고양이집사 ")

            player = credentials.player
            assert (player.id, player.kind, player.nickname) == ("p1", PlayerKind.GUEST, "고양이집사")
            assert (player.skin_1p, player.skin_2p) == (16, 17)
            assert service.authenticate(credentials.token) is player

        def test_실패_닉네임이_규칙에_맞지_않으면_거부한다(self, service):
            with pytest.raises(InvalidInput):
                service.create_guest("냥")

    class TestAuthenticate:
        def test_실패_저장소에_없는_플레이어의_토큰이면_거부한다(self, service):
            token = SignedTokenIssuer("secret").issue("ghost")

            with pytest.raises(Unauthorized):
                service.authenticate(token)

    class TestGetPlayer:
        def test_실패_없는_플레이어면_거부한다(self, service):
            with pytest.raises(PlayerNotFound):
                service.get_player("ghost")
