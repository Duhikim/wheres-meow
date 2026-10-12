from sqlalchemy import select

from integration_support import build_app_env, connect, create_guest, received
from wheresmeow.game.adapter.outbound.persistence.models import GameRecordRow


def start_invite_game(app_env):
    token_a, id_a = create_guest(app_env, "방장냥")
    token_b, id_b = create_guest(app_env, "손님냥")
    code = app_env.http.post("/api/rooms", headers={"Authorization": f"Bearer {token_a}"}).get_json()["code"]
    a, b = connect(app_env, token_a), connect(app_env, token_b)
    a.emit("room:join", {"code": code})
    b.emit("room:join", {"code": code})
    game_id = received(a, "game:started")[0]["gameId"]
    received(b, "game:started")
    return {"a": a, "b": b, "token_a": token_a, "token_b": token_b, "game_id": game_id}


def auth(token):
    return {"Authorization": f"Bearer {token}"}


class TestCurrentGameApi:
    class TestGet:
        def test_성공_진행_중인_대국이_없으면_204(self, app_env):
            token, _ = create_guest(app_env, "냥냥이")

            assert app_env.http.get("/api/games/current", headers=auth(token)).status_code == 204

        def test_성공_진행_중인_대국의_ID를_돌려준다(self, app_env):
            g = start_invite_game(app_env)

            response = app_env.http.get("/api/games/current", headers=auth(g["token_b"]))

            assert response.status_code == 200
            assert response.get_json() == {"gameId": g["game_id"]}

        def test_실패_토큰이_없으면_401(self, app_env):
            assert app_env.http.get("/api/games/current").status_code == 401


class TestGameSync:
    class TestSync:
        def test_성공_요청한_사람에게만_현재_상태_전체를_보낸다(self, app_env):
            g = start_invite_game(app_env)
            g["a"].emit("game:reveal", {"gameId": g["game_id"], "x": 0, "y": 0})
            received(g["a"], "game:revealed")
            received(g["b"], "game:revealed")
            reconnected = connect(app_env, g["token_b"])  # 새로고침한 탭

            reconnected.emit("game:sync", {"gameId": g["game_id"]})

            [state] = received(reconnected, "game:state")
            assert (state["gameId"], state["mySeat"], state["status"], state["version"]) == (g["game_id"], 1, "IN_PROGRESS", 1)
            assert len(state["cells"]) > 1
            assert "cats" not in state
            assert received(g["a"], "game:state") == []

        def test_성공_끝난_대국은_결과와_고양이_위치까지_보낸다(self, app_env):
            g = start_invite_game(app_env)
            g["b"].emit("game:forfeit", {"gameId": g["game_id"]})

            g["a"].emit("game:sync", {"gameId": g["game_id"]})

            [state] = received(g["a"], "game:state")
            assert state["status"] == "FINISHED"
            assert state["result"] == {
                "reason": "FORFEIT",
                "winner": 0,
                "ratingChanges": [{"before": 1000, "after": 1016}, {"before": 1000, "after": 984}],
            }
            assert len(state["cats"]) == 25

        def test_실패_참가자가_아니면_거부한다(self, app_env):
            g = start_invite_game(app_env)
            token_c, _ = create_guest(app_env, "구경냥")
            c = connect(app_env, token_c)

            c.emit("game:sync", {"gameId": g["game_id"]})

            assert [e["code"] for e in received(c, "error")] == ["NOT_A_PARTICIPANT"]
            assert received(c, "game:state") == []

        def test_실패_없는_대국이면_GAME_NOT_FOUND(self, app_env):
            token, _ = create_guest(app_env, "냥냥이")
            client = connect(app_env, token)

            client.emit("game:sync", {"gameId": "nope"})

            assert [e["code"] for e in received(client, "error")] == ["GAME_NOT_FOUND"]


class TestPersistence:
    class TestRestart:
        def test_성공_서버를_다시_띄워도_게스트와_내_고양이_설정이_유지된다(self, app_env):
            token, player_id = create_guest(app_env, "냥냥이")
            app_env.http.put("/api/players/me/skins", json={"skin1p": 9, "skin2p": 12}, headers=auth(token))

            restarted = build_app_env(database=app_env.database)
            response = restarted.http.get("/api/players/me", headers=auth(token))

            assert response.status_code == 200
            body = response.get_json()
            assert (body["id"], body["skin1p"], body["skin2p"]) == (player_id, 9, 12)

        def test_성공_끝난_대국이_DB에_기록된다(self, app_env):
            g = start_invite_game(app_env)

            g["a"].emit("game:forfeit", {"gameId": g["game_id"]})

            with app_env.database.session() as s:
                row = s.scalars(select(GameRecordRow)).one()
            assert (row.id, row.end_reason, row.winner_seat) == (g["game_id"], "FORFEIT", 1)


class TestTokenRefresh:
    class TestGetMe:
        def test_성공_내_정보를_조회하면_새_토큰을_함께_준다(self, app_env):
            token, _ = create_guest(app_env, "냥냥이")
            app_env.clock.advance(5_000)

            body = app_env.http.get("/api/players/me", headers=auth(token)).get_json()

            assert body["token"]
            assert app_env.http.get("/api/players/me", headers=auth(body["token"])).status_code == 200
