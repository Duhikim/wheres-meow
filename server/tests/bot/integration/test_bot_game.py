from integration_support import connect, create_guest, received


def auth(token):
    return {"Authorization": f"Bearer {token}"}


class TestBotGame:
    class TestStart:
        def test_성공_봇_대국을_시작하면_봇_좌석과_사람의_2P_스킨으로_시작한다(self, app_env):
            token, _ = create_guest(app_env, "사람냥")
            app_env.http.put("/api/players/me/skins", json={"skin1p": 9, "skin2p": 21}, headers=auth(token))
            client = connect(app_env, token)

            client.emit("bot:start", {"difficulty": "NORMAL"})

            [game] = received(client, "game:started")
            assert game["mode"] == "BOT"
            assert game["mySeat"] == 0
            assert [s["nickname"] for s in game["seats"]] == ["사람냥", "컴퓨터 (보통)"]
            assert [s["skin"] for s in game["seats"]] == [9, 21]

        def test_실패_모르는_난이도면_오류를_받는다(self, app_env):
            token, _ = create_guest(app_env, "사람냥")
            client = connect(app_env, token)

            client.emit("bot:start", {"difficulty": "GOD"})

            assert [e["code"] for e in received(client, "error")] == ["INVALID_INPUT"]

    class TestPlay:
        def test_성공_봇_대국에서_기권하면_봇_전적에_패배로_남는다(self, app_env):
            token, _ = create_guest(app_env, "사람냥")
            client = connect(app_env, token)
            client.emit("bot:start", {"difficulty": "EASY"})
            game_id = received(client, "game:started")[0]["gameId"]

            app_env.bot_scheduler.run_all()  # 통합 환경의 선공은 항상 좌석 0(사람)이라 봇은 아직 두지 않는다
            client.emit("game:forfeit", {"gameId": game_id})

            records = app_env.http.get("/api/players/me/bot-records", headers=auth(token)).get_json()
            easy = next(r for r in records if r["difficulty"] == "EASY")
            assert (easy["wins"], easy["losses"], easy["draws"]) == (0, 1, 0)

        def test_성공_사람이_숫자_칸을_열면_봇이_이어서_둔다(self, app_env):
            token, _ = create_guest(app_env, "사람냥")
            client = connect(app_env, token)
            client.emit("bot:start", {"difficulty": "HARD"})
            game_id = received(client, "game:started")[0]["gameId"]

            client.emit("game:reveal", {"gameId": game_id, "x": 5, "y": 9})  # 숫자 칸 → 봇 차례
            received(client, "game:revealed")
            app_env.bot_scheduler.run_all()

            [bot_move, *_] = received(client, "game:revealed")
            assert bot_move["seat"] == 1

    class TestRecordsApi:
        def test_실패_토큰이_없으면_401(self, app_env):
            assert app_env.http.get("/api/players/me/bot-records").status_code == 401
