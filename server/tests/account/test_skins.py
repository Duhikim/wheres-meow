import pytest

from wheresmeow.account.adapter.outbound.memory.in_memory_player_store import InMemoryPlayerStore
from wheresmeow.account.adapter.outbound.token.signed_token_issuer import SignedTokenIssuer
from wheresmeow.account.application.service.guest_service import GuestService, PlayerNotFound
from wheresmeow.account.domain.player import InvalidSkin, Player, PlayerKind


class TestPlayer:
    class TestChangeSkins:
        def test_성공_허용된_서로_다른_두_스킨으로_바꾼다(self):
            player = Player("p1", PlayerKind.GUEST, "냥냥이")

            player.change_skins(9, 21)

            assert (player.skin_1p, player.skin_2p) == (9, 21)

        @pytest.mark.parametrize("skins", [(13, 16), (16, 0), (8, 9)])
        def test_실패_허용하지_않는_스킨이면_거부하고_그대로_둔다(self, skins):
            player = Player("p1", PlayerKind.GUEST, "냥냥이")

            with pytest.raises(InvalidSkin):
                player.change_skins(*skins)
            assert (player.skin_1p, player.skin_2p) == (16, 17)

        def test_실패_1P와_2P가_같으면_거부한다(self):
            with pytest.raises(InvalidSkin):
                Player("p1", PlayerKind.GUEST, "냥냥이").change_skins(18, 18)


class TestGuestService:
    @pytest.fixture
    def service(self):
        return GuestService(InMemoryPlayerStore(), SignedTokenIssuer("secret"), id_factory=lambda: "p1")

    class TestChangeSkins:
        def test_성공_바꾼_스킨이_저장된다(self, service):
            service.create_guest("냥냥이")

            service.change_skins("p1", 20, 16)

            player = service.get_player("p1")
            assert (player.skin_1p, player.skin_2p) == (20, 16)

        def test_실패_없는_플레이어면_거부한다(self, service):
            with pytest.raises(PlayerNotFound):
                service.change_skins("ghost", 20, 16)
