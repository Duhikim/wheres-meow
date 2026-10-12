from integration_support import create_guest


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


class TestPracticeApi:
    class TestSubmit:
        def test_성공_클리어_시간을_보내면_최고_기록과_갱신_여부를_돌려준다(self, app_env):
            token, _ = create_guest(app_env, "연습냥")

            first = app_env.http.post(
                "/api/players/me/single-records", json={"difficulty": "BEGINNER", "elapsedMs": 41_234}, headers=auth(token)
            )
            slower = app_env.http.post(
                "/api/players/me/single-records", json={"difficulty": "BEGINNER", "elapsedMs": 60_000}, headers=auth(token)
            )

            assert first.status_code == 200
            assert first.get_json() == {"difficulty": "BEGINNER", "bestMs": 41_234, "newBest": True, "clears": 1}
            assert slower.get_json() == {"difficulty": "BEGINNER", "bestMs": 41_234, "newBest": False, "clears": 2}

        def test_실패_시간이_정수가_아니면_INVALID_INPUT(self, app_env):
            token, _ = create_guest(app_env, "연습냥")

            response = app_env.http.post(
                "/api/players/me/single-records", json={"difficulty": "BEGINNER", "elapsedMs": "41"}, headers=auth(token)
            )

            assert response.status_code == 400
            assert response.get_json()["code"] == "INVALID_INPUT"

        def test_실패_로그인하지_않으면_401(self, app_env):
            response = app_env.http.post("/api/players/me/single-records", json={"difficulty": "BEGINNER", "elapsedMs": 41_000})

            assert response.status_code == 401

    class TestRead:
        def test_성공_내_기록과_공개_프로필에서_난이도별_최고_기록을_본다(self, app_env):
            token, player_id = create_guest(app_env, "연습냥")
            app_env.http.post(
                "/api/players/me/single-records", json={"difficulty": "EXPERT", "elapsedMs": 300_000}, headers=auth(token)
            )

            mine = app_env.http.get("/api/players/me/single-records", headers=auth(token)).get_json()
            profile = app_env.http.get(f"/api/players/{player_id}").get_json()

            assert mine[2] == {"difficulty": "EXPERT", "bestMs": 300_000, "clears": 1}
            assert profile["singleRecords"] == mine
