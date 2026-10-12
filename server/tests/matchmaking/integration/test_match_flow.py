from integration_support import connect, create_guest, received


def queued_guest(app_env, nickname: str):
    token, player_id = create_guest(app_env, nickname)
    client = connect(app_env, token)
    client.emit("match:join")
    return client, player_id


class TestMatchFlow:
    class TestJoin:
        def test_성공_대기열에_들어가면_대기_시작_시각과_범위를_받는다(self, app_env):
            a, _ = queued_guest(app_env, "에이냥")

            [waiting] = received(a, "match:waiting")
            assert waiting == {"since": 0, "range": 100}

        def test_실패_두_번_들어가면_ALREADY_QUEUED(self, app_env):
            a, _ = queued_guest(app_env, "에이냥")

            a.emit("match:join")

            assert [e["code"] for e in received(a, "error")] == ["ALREADY_QUEUED"]

    class TestPairing:
        def test_성공_두_사람이_기다리면_다음_틱에_매칭_대국이_시작되고_먼저_온_사람이_우선권자다(self, app_env):
            a, _ = queued_guest(app_env, "에이냥")
            app_env.clock.advance(500)
            b, _ = queued_guest(app_env, "비냥")

            app_env.match_repeater.tick()

            [started_a] = received(a, "game:started")
            [started_b] = received(b, "game:started")
            assert started_a["gameId"] == started_b["gameId"]
            assert started_a["mode"] == "MATCH"
            assert (started_a["mySeat"], started_b["mySeat"]) == (0, 1)
            assert [s["nickname"] for s in started_a["seats"]] == ["에이냥", "비냥"]

        def test_성공_매칭_대국도_레이팅에_반영된다(self, app_env):
            a, _ = queued_guest(app_env, "에이냥")
            b, _ = queued_guest(app_env, "비냥")
            app_env.match_repeater.tick()
            game_id = received(a, "game:started")[0]["gameId"]

            b.emit("game:forfeit", {"gameId": game_id})

            [ended] = received(a, "game:ended")
            assert ended["ratingChanges"][0]["after"] == 1016

        def test_성공_혼자면_대국이_시작되지_않는다(self, app_env):
            a, _ = queued_guest(app_env, "에이냥")

            app_env.match_repeater.tick()

            assert received(a, "game:started") == []

    class TestLeave:
        def test_성공_대기를_취소하면_짝지어지지_않는다(self, app_env):
            a, _ = queued_guest(app_env, "에이냥")
            a.emit("match:leave")
            b, _ = queued_guest(app_env, "비냥")

            app_env.match_repeater.tick()

            assert received(b, "game:started") == []

        def test_성공_연결이_끊기면_대기열에서_빠진다(self, app_env):
            a, _ = queued_guest(app_env, "에이냥")
            a.disconnect()
            b, _ = queued_guest(app_env, "비냥")

            app_env.match_repeater.tick()

            assert received(b, "game:started") == []

        def test_실패_대국_중이면_대기열에_들어갈_수_없다(self, app_env):
            a, _ = queued_guest(app_env, "에이냥")
            queued_guest(app_env, "비냥")
            app_env.match_repeater.tick()
            received(a, "error")

            a.emit("match:join")

            assert [e["code"] for e in received(a, "error")] == ["ALREADY_IN_GAME"]

        def test_성공_같은_플레이어의_다른_연결이_남아_있으면_대기열에서_빼지_않는다(self, app_env):
            token_a, _ = create_guest(app_env, "에이냥")
            old = connect(app_env, token_a)
            old.emit("match:join")
            new = connect(app_env, token_a)  # 망 전환 등으로 새 연결이 먼저 붙었다
            new.emit("match:join")
            assert [e["code"] for e in received(new, "error")] == ["ALREADY_QUEUED"]

            old.disconnect()  # 옛 연결은 뒤늦게 정리된다
            b, _ = queued_guest(app_env, "비냥")
            app_env.match_repeater.tick()

            assert len(received(new, "game:started")) == 1
            assert len(received(b, "game:started")) == 1
