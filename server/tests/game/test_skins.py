import pytest

from wheresmeow.game.domain.errors import InvalidSkin
from wheresmeow.game.domain.skins import SkinPreference, assign_skins


class TestSkinPreference:
    class TestInit:
        def test_성공_기본값은_16과_17이다(self):
            pref = SkinPreference()

            assert (pref.skin_1p, pref.skin_2p) == (16, 17)

        def test_실패_허용하지_않는_스킨이면_거부한다(self):
            with pytest.raises(InvalidSkin):
                SkinPreference(13, 16)

        def test_실패_1P와_2P가_같으면_거부한다(self):
            with pytest.raises(InvalidSkin):
                SkinPreference(9, 9)


class TestAssignSkins:
    class TestAssign:
        def test_성공_1P가_다르면_둘_다_1P를_쓴다(self):
            assert assign_skins(SkinPreference(16, 17), SkinPreference(18, 19)) == (16, 18)

        def test_성공_1P가_겹치면_우선권_없는_쪽이_2P를_쓴다(self):
            assert assign_skins(SkinPreference(16, 17), SkinPreference(16, 20)) == (16, 20)

        def test_성공_상대의_2P가_우선권자의_1P와_같아도_겹치지_않는다(self):
            # 상대 1P(17) 가 우선권자 1P(16) 와 다르므로 상대는 1P 를 쓴다
            assert assign_skins(SkinPreference(16, 17), SkinPreference(17, 16)) == (16, 17)
