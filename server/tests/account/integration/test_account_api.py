from integration_support import create_guest


class TestAccountApi:
    class TestPostGuests:
        def test_성공_게스트를_만들고_토큰과_플레이어를_돌려준다(self, app_env):
            response = app_env.http.post("/api/guests", json={"nickname": "고양이집사"})

            assert response.status_code == 201
            body = response.get_json()
            assert body["token"]
            assert body["player"]["nickname"] == "고양이집사"
            assert body["player"]["kind"] == "GUEST"
            assert (body["player"]["skin1p"], body["player"]["skin2p"]) == (16, 17)

        def test_실패_닉네임이_규칙에_맞지_않으면_400(self, app_env):
            response = app_env.http.post("/api/guests", json={"nickname": "냥"})

            assert response.status_code == 400
            assert response.get_json()["code"] == "INVALID_INPUT"

        def test_실패_본문이_없으면_400(self, app_env):
            response = app_env.http.post("/api/guests")

            assert response.status_code == 400
            assert response.get_json()["code"] == "INVALID_INPUT"

    class TestGetMe:
        def test_성공_토큰으로_내_정보를_조회한다(self, app_env):
            token, player_id = create_guest(app_env, "냥냥이")

            response = app_env.http.get("/api/players/me", headers={"Authorization": f"Bearer {token}"})

            assert response.status_code == 200
            assert response.get_json()["id"] == player_id

        def test_실패_토큰이_없으면_401(self, app_env):
            response = app_env.http.get("/api/players/me")

            assert response.status_code == 401
            assert response.get_json()["code"] == "UNAUTHORIZED"

        def test_실패_위조된_토큰이면_401(self, app_env):
            response = app_env.http.get("/api/players/me", headers={"Authorization": "Bearer forged"})

            assert response.status_code == 401
