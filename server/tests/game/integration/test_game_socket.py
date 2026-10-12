from integration_support import connect, create_guest, received


class TestGameSocket:
    class TestConnect:
        def test_실패_토큰이_없으면_연결을_거부한다(self, app_env):
            assert not connect(app_env, None).is_connected()

        def test_실패_위조된_토큰이면_연결을_거부한다(self, app_env):
            assert not connect(app_env, "forged").is_connected()

    class TestReveal:
        def test_실패_좌표가_정수가_아니면_INVALID_INPUT(self, app_env):
            token, _ = create_guest(app_env, "냥냥이")
            client = connect(app_env, token)

            client.emit("game:reveal", {"gameId": "g", "x": "1", "y": 0})

            assert [e["code"] for e in received(client, "error")] == ["INVALID_INPUT"]

        def test_실패_없는_대국이면_GAME_NOT_FOUND(self, app_env):
            token, _ = create_guest(app_env, "냥냥이")
            client = connect(app_env, token)

            client.emit("game:reveal", {"gameId": "nope", "x": 0, "y": 0})

            assert [e["code"] for e in received(client, "error")] == ["GAME_NOT_FOUND"]
