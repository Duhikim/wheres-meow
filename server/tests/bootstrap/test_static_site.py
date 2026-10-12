import pytest

from wheresmeow.bootstrap.app_factory import create_app
from wheresmeow.bootstrap.config import AppConfig


@pytest.fixture
def static_dir(tmp_path):
    (tmp_path / "index.html").write_text("<!doctype html><title>Where's Meow</title>")
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "app.js").write_text("console.log('app')")
    return tmp_path


@pytest.fixture
def http(static_dir):
    app, _ = create_app(AppConfig(env="test", secret_key="s", static_dir=str(static_dir)))
    return app.test_client()


class TestStaticSite:
    class TestIndex:
        def test_성공_첫_화면에서_index_html을_돌려준다(self, http):
            response = http.get("/")

            assert response.status_code == 200
            assert b"Where's Meow" in response.data

        @pytest.mark.parametrize("path", ["/r/ABCDEF", "/play/g1", "/ranking"])
        def test_성공_화면_경로를_새로고침해도_index_html을_돌려준다(self, http, path):
            response = http.get(path)

            assert response.status_code == 200
            assert b"Where's Meow" in response.data

    class TestAssets:
        def test_성공_빌드된_자산_파일을_그대로_돌려준다(self, http):
            response = http.get("/assets/app.js")

            assert response.status_code == 200
            assert response.data == b"console.log('app')"

    class TestApi:
        def test_실패_없는_API_경로는_index_html이_아니라_404다(self, http):
            response = http.get("/api/nope")

            assert response.status_code == 404
            assert b"Where's Meow" not in response.data

        def test_성공_기존_API는_그대로_동작한다(self, http):
            response = http.post("/api/guests", json={"nickname": "고양이집사"})

            assert response.status_code == 201


class TestHealth:
    class TestGet:
        def test_성공_정적_파일_설정과_무관하게_상태_확인에_응답한다(self):
            app, _ = create_app(AppConfig(env="test", secret_key="s"))

            response = app.test_client().get("/api/health")

            assert response.status_code == 200
            assert response.get_json() == {"status": "ok"}
