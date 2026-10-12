import pytest

from integration_support import connect, create_guest, received


@pytest.fixture
def started(app_env):
    """방장 A 와 손님 B 가 초대 방으로 대국을 시작한 상태."""
    token_a, _ = create_guest(app_env, "방장냥")
    token_b, _ = create_guest(app_env, "손님냥")
    code = app_env.http.post("/api/rooms", headers={"Authorization": f"Bearer {token_a}"}).get_json()["code"]
    a, b = connect(app_env, token_a), connect(app_env, token_b)
    a.emit("room:join", {"code": code})
    waiting = received(a, "room:waiting")
    b.emit("room:join", {"code": code})
    started_a, started_b = received(a, "game:started"), received(b, "game:started")
    return {
        "a": a,
        "b": b,
        "token_a": token_a,
        "code": code,
        "waiting": waiting,
        "started_a": started_a,
        "started_b": started_b,
    }


class TestInviteGameFlow:
    class TestStart:
        def test_성공_방장은_대기하고_상대가_오면_두_사람_모두_대국_시작을_받는다(self, started):
            assert started["waiting"][0]["code"] == started["code"]
            [game_a], [game_b] = started["started_a"], started["started_b"]
            assert game_a["gameId"] == game_b["gameId"]
            assert (game_a["mySeat"], game_b["mySeat"]) == (0, 1)
            assert [s["nickname"] for s in game_a["seats"]] == ["방장냥", "손님냥"]

        def test_성공_1P가_겹치면_손님이_2P_스킨을_쓴다(self, started):
            [game] = started["started_a"]

            assert [s["skin"] for s in game["seats"]] == [16, 17]

        def test_성공_시작_페이로드에_고양이_위치가_없다(self, started):
            [game] = started["started_b"]

            assert "cats" not in game
            assert game["cells"] == []

    class TestPlay:
        def test_성공_고양이를_찾고_빈_칸을_열고_기권까지_진행한다(self, started):
            a, b = started["a"], started["b"]
            game_id = started["started_a"][0]["gameId"]

            a.emit("game:reveal", {"gameId": game_id, "x": 11, "y": 9})
            a.emit("game:reveal", {"gameId": game_id, "x": 0, "y": 0})
            b.emit("game:forfeit", {"gameId": game_id})

            revealed = received(b, "game:revealed")
            assert revealed[0]["cells"] == [{"x": 11, "y": 9, "kind": "cat", "seat": 0}]
            assert revealed[0]["currentSeat"] == 0
            assert len(revealed[1]["cells"]) > 1
            assert revealed[1]["currentSeat"] == 1
            [ended] = received(a, "game:ended")
            assert (ended["reason"], ended["winner"], ended["version"]) == ("FORFEIT", 0, 3)
            assert len(ended["cats"]) == 25

        def test_성공_턴_시간이_지나면_두_사람_모두_감점_이벤트를_받는다(self, app_env, started):
            app_env.timer.fire_latest()

            [timeout_a] = received(started["a"], "game:timeout")
            [timeout_b] = received(started["b"], "game:timeout")
            assert timeout_a == timeout_b
            assert (timeout_a["scores"], timeout_a["currentSeat"]) == ([-1, 0], 1)

        def test_성공_같은_플레이어가_탭을_두_개_열면_두_탭_모두_이벤트를_받는다(self, app_env, started):
            token_a = started["token_a"]
            second_tab = connect(app_env, token_a)
            game_id = started["started_a"][0]["gameId"]

            started["a"].emit("game:reveal", {"gameId": game_id, "x": 11, "y": 9})

            assert len(received(second_tab, "game:revealed")) == 1

        def test_실패_자기_차례가_아니면_요청한_사람만_오류를_받는다(self, started):
            a, b = started["a"], started["b"]
            game_id = started["started_a"][0]["gameId"]

            b.emit("game:reveal", {"gameId": game_id, "x": 0, "y": 0})

            assert [e["code"] for e in received(b, "error")] == ["NOT_YOUR_TURN"]
            assert received(a, "error") == []

        def test_실패_대국이_시작된_방에_세_번째_사람이_오면_오류를_받는다(self, app_env, started):
            token_c, _ = create_guest(app_env, "구경냥")
            c = connect(app_env, token_c)

            c.emit("room:join", {"code": started["code"]})

            assert [e["code"] for e in received(c, "error")] == ["ROOM_FULL"]


class TestRoomApi:
    class TestGetRoom:
        def test_성공_방_상태를_조회한다(self, app_env):
            token, _ = create_guest(app_env, "방장냥")
            code = app_env.http.post("/api/rooms", headers={"Authorization": f"Bearer {token}"}).get_json()["code"]

            response = app_env.http.get(f"/api/rooms/{code}")

            assert response.status_code == 200
            assert response.get_json()["status"] == "WAITING"

        def test_실패_없는_방이면_404(self, app_env):
            response = app_env.http.get("/api/rooms/ZZZZZZ")

            assert response.status_code == 404
            assert response.get_json()["code"] == "ROOM_NOT_FOUND"

    class TestPostRoom:
        def test_실패_토큰이_없으면_401(self, app_env):
            assert app_env.http.post("/api/rooms").status_code == 401

    class TestJoinSocket:
        def test_실패_없는_방_코드면_오류를_받는다(self, app_env):
            token, _ = create_guest(app_env, "길잃은냥")
            client = connect(app_env, token)

            client.emit("room:join", {"code": "ZZZZZZ"})

            assert [e["code"] for e in received(client, "error")] == ["ROOM_NOT_FOUND"]
