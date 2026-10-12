from integration_support import connect, create_guest, received


def finished_invite_game(app_env):
    token_a, _ = create_guest(app_env, "방장냥")
    token_b, _ = create_guest(app_env, "손님냥")
    code = app_env.http.post("/api/rooms", headers={"Authorization": f"Bearer {token_a}"}).get_json()["code"]
    a, b = connect(app_env, token_a), connect(app_env, token_b)
    a.emit("room:join", {"code": code})
    b.emit("room:join", {"code": code})
    [started] = received(a, "game:started")
    received(b, "game:started")
    b.emit("game:forfeit", {"gameId": started["gameId"]})
    received(a, "game:ended")
    received(b, "game:ended")
    return a, b, started


class TestRematchFlow:
    class TestAccept:
        def test_성공_요청과_수락으로_선공을_바꾼_같은_좌석의_새_대국이_시작된다(self, app_env):
            a, b, previous = finished_invite_game(app_env)

            a.emit("game:rematch-request", {"gameId": previous["gameId"]})
            assert received(b, "game:rematch-requested") == [{"gameId": previous["gameId"]}]
            b.emit("game:rematch-request", {"gameId": previous["gameId"]})

            [started_a] = received(a, "game:started")
            [started_b] = received(b, "game:started")
            assert started_a["gameId"] == started_b["gameId"] != previous["gameId"]
            assert started_a["mode"] == "INVITE"
            assert started_a["seats"] == [{**s, "score": 0} for s in previous["seats"]]
            assert (previous["currentSeat"], started_a["currentSeat"]) == (0, 1)

    class TestDecline:
        def test_성공_거절하면_요청한_사람이_취소_사유를_받는다(self, app_env):
            a, b, previous = finished_invite_game(app_env)
            a.emit("game:rematch-request", {"gameId": previous["gameId"]})

            b.emit("game:rematch-decline", {"gameId": previous["gameId"]})

            assert received(a, "game:rematch-cancelled") == [{"gameId": previous["gameId"], "reason": "DECLINED"}]

        def test_실패_상대가_결과_화면을_떠난_뒤에는_REMATCH_EXPIRED(self, app_env):
            a, b, previous = finished_invite_game(app_env)
            b.emit("game:leave-result", {"gameId": previous["gameId"]})
            assert received(a, "game:rematch-cancelled") == [{"gameId": previous["gameId"], "reason": "LEFT"}]

            a.emit("game:rematch-request", {"gameId": previous["gameId"]})

            assert [e["code"] for e in received(a, "error")] == ["REMATCH_EXPIRED"]

    class TestExpiry:
        def test_성공_30초가_지나면_두_사람_모두_만료를_받는다(self, app_env):
            a, b, previous = finished_invite_game(app_env)
            a.emit("game:rematch-request", {"gameId": previous["gameId"]})
            app_env.clock.advance(30_000)

            app_env.timer.fire_latest()

            expired = {"gameId": previous["gameId"], "reason": "EXPIRED"}
            assert received(a, "game:rematch-cancelled") == [expired]
            assert received(b, "game:rematch-cancelled") == [expired]

    class TestBot:
        def test_성공_컴퓨터_대전은_요청하자마자_새_대국이_시작된다(self, app_env):
            token, _ = create_guest(app_env, "사람냥")
            client = connect(app_env, token)
            client.emit("bot:start", {"difficulty": "EASY"})
            [first] = received(client, "game:started")
            client.emit("game:forfeit", {"gameId": first["gameId"]})
            received(client, "game:ended")

            client.emit("game:rematch-request", {"gameId": first["gameId"]})

            [second] = received(client, "game:started")
            assert second["mode"] == "BOT" and second["gameId"] != first["gameId"]
