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

        def test_실패_운영_환경이_gevent가_아니면_시작을_거부한다(self):
            with pytest.raises(ValueError):
                AppConfig(env="production", secret_key="real-secret", async_mode="threading")

        def test_성공_운영_환경은_서명_키와_gevent와_PostgreSQL_로_시작한다(self):
            config = AppConfig(
                env="production", secret_key="real-secret", async_mode="gevent", database_url="postgresql://u:p@h/db"
            )

            assert config.env == "production"

        def test_실패_정적_파일_폴더에_index_html이_없으면_거부한다(self, tmp_path):
            with pytest.raises(ValueError):
                AppConfig(static_dir=str(tmp_path))

    class TestDatabaseUrl:
        def test_성공_개발_환경_기본값은_SQLite_파일이다(self):
            assert AppConfig.from_env({}).database_url.startswith("sqlite:///")

        def test_성공_DATABASE_URL_을_읽는다(self):
            config = AppConfig.from_env({"DATABASE_URL": "postgresql://u:p@h/db"})

            assert config.database_url == "postgresql://u:p@h/db"

        def test_실패_운영_환경에_PostgreSQL_주소가_없으면_시작을_거부한다(self):
            with pytest.raises(ValueError):
                AppConfig(env="production", secret_key="real-secret", async_mode="gevent")

        def test_실패_운영_환경에서_SQLite_를_쓰면_시작을_거부한다(self):
            with pytest.raises(ValueError):
                AppConfig(env="production", secret_key="real-secret", async_mode="gevent", database_url="sqlite:///x.db")

    class TestFromEnvStatic:
        def test_성공_정적_파일_폴더를_읽는다(self, tmp_path):
            (tmp_path / "index.html").write_text("ok")

            config = AppConfig.from_env({"WHERESMEOW_STATIC_DIR": str(tmp_path)})

            assert config.static_dir == str(tmp_path)
