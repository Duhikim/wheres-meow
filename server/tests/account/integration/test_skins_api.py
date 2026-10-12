from integration_support import connect, create_guest, received


def put_skins(app_env, token, body):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return app_env.http.put("/api/players/me/skins", json=body, headers=headers)


class TestSkinsApi:
    class TestPutSkins:
        def test_성공_스킨을_바꾸면_바뀐_내_정보를_돌려준다(self, app_env):
            token, _ = create_guest(app_env, "냥냥이")

            response = put_skins(app_env, token, {"skin1p": 9, "skin2p": 12})

            assert response.status_code == 200
            assert (response.get_json()["skin1p"], response.get_json()["skin2p"]) == (9, 12)

        def test_실패_같은_스킨_두_개면_400_INVALID_SKIN(self, app_env):
            token, _ = create_guest(app_env, "냥냥이")

            response = put_skins(app_env, token, {"skin1p": 9, "skin2p": 9})

            assert response.status_code == 400
            assert response.get_json()["code"] == "INVALID_SKIN"

        def test_실패_숫자가_아니면_400_INVALID_INPUT(self, app_env):
            token, _ = create_guest(app_env, "냥냥이")

            response = put_skins(app_env, token, {"skin1p": "9", "skin2p": 12})

            assert response.status_code == 400
            assert response.get_json()["code"] == "INVALID_INPUT"

        def test_실패_토큰이_없으면_401(self, app_env):
            assert put_skins(app_env, None, {"skin1p": 9, "skin2p": 12}).status_code == 401

        def test_실패_토큰도_본문도_없으면_입력_검증보다_인증_실패가_먼저다(self, app_env):
            response = app_env.http.put("/api/players/me/skins")

            assert response.status_code == 401

    class TestAppliedToGame:
        def test_성공_바꾼_스킨이_다음_대국에_쓰인다(self, app_env):
            token_a, _ = create_guest(app_env, "방장냥")
            token_b, _ = create_guest(app_env, "손님냥")
            put_skins(app_env, token_a, {"skin1p": 9, "skin2p": 10})
            put_skins(app_env, token_b, {"skin1p": 9, "skin2p": 21})
            code = app_env.http.post("/api/rooms", headers={"Authorization": f"Bearer {token_a}"}).get_json()["code"]
            a, b = connect(app_env, token_a), connect(app_env, token_b)

            a.emit("room:join", {"code": code})
            b.emit("room:join", {"code": code})

            [game] = received(a, "game:started")
            assert [s["skin"] for s in game["seats"]] == [9, 21]  # 1P 가 겹쳐 손님은 2P(21)
