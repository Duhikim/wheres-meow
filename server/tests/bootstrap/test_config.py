import pytest

from wheresmeow.bootstrap.config import AppConfig


class TestAppConfig:
    class TestFromEnv:
        def test_성공_환경_변수를_읽는다(self):
            config = AppConfig.from_env(
                {"WHERESMEOW_ENV": "test", "WHERESMEOW_SECRET_KEY": "s", "WHERESMEOW_TEST_SEED": "7"}
            )

            assert (config.env, config.secret_key, config.test_seed) == ("test", "s", 7)

        def test_성공_값이_없으면_개발_환경_기본값을_쓴다(self):
            config = AppConfig.from_env({})

            assert (config.env, config.test_seed, config.async_mode) == ("development", None, "threading")

    class TestValidate:
        def test_실패_운영_환경에_서명_키가_없으면_시작을_거부한다(self):
            with pytest.raises(ValueError):
                AppConfig.from_env({"WHERESMEOW_ENV": "production"})

        def test_실패_운영_환경에_테스트_시드가_켜져_있으면_시작을_거부한다(self):
            with pytest.raises(ValueError):
                AppConfig(env="production", secret_key="real-secret", test_seed=1)

        def test_실패_알_수_없는_환경이면_거부한다(self):
            with pytest.raises(ValueError):
                AppConfig(env="staging")
