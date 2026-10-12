from integration_support import connect, create_guest, received


def signup(app_env, username: str, nickname: str) -> tuple[str, str]:
    response = app_env.http.post(
        "/api/auth/signup", json={"username": username, "password": "password1", "nickname": nickname}
    )
    assert response.status_code == 201, response.get_json()
    body = response.get_json()
    return body["token"], body["player"]["id"]


def play_invite(app_env, host: tuple, guest: tuple, loser: str) -> dict:
    """host·guest 는 (token, socket client). loser 쪽이 기권한다. game:ended 페이로드를 돌려준다."""
    (token_a, a), (_, b) = host, guest
    code = app_env.http.post("/api/rooms", headers={"Authorization": f"Bearer {token_a}"}).get_json()["code"]
    a.emit("room:join", {"code": code})
    b.emit("room:join", {"code": code})
    game_id = received(a, "game:started")[0]["gameId"]
    received(b, "game:started")
    (a if loser == "host" else b).emit("game:forfeit", {"gameId": game_id})
    received(b, "game:ended")
    return received(a, "game:ended")[0]


class TestRatingApi:
    class TestRatingOnGameEnd:
        def test_성공_사람_간_대국이_끝나면_game_ended_에_레이팅_변화가_실린다(self, app_env):
            token_a, _ = create_guest(app_env, "방장냥")
            token_b, _ = create_guest(app_env, "손님냥")
            host, guest = (token_a, connect(app_env, token_a)), (token_b, connect(app_env, token_b))

            ended = play_invite(app_env, host, guest, loser="guest")

            assert ended["ratingChanges"] == [{"before": 1000, "after": 1016}, {"before": 1000, "after": 984}]

    class TestRankings:
        def test_성공_아무도_없으면_빈_첫_쪽이다(self, app_env):
            response = app_env.http.get("/api/rankings")

            assert response.status_code == 200
            assert response.get_json() == {"page": 1, "totalPages": 1, "entries": []}

        def test_성공_회원이_5판을_채우면_레이팅_순으로_나온다(self, app_env):
            token_a, id_a = signup(app_env, "neko_a", "에이냥")
            token_b, id_b = signup(app_env, "neko_b", "비냥")
            host, guest = (token_a, connect(app_env, token_a)), (token_b, connect(app_env, token_b))
            for _ in range(4):
                play_invite(app_env, host, guest, loser="guest")
            assert app_env.http.get("/api/rankings").get_json()["entries"] == []  # 아직 4판

            play_invite(app_env, host, guest, loser="guest")

            entries = app_env.http.get("/api/rankings?page=1").get_json()["entries"]
            assert [(e["rank"], e["playerId"], e["nickname"]) for e in entries] == [(1, id_a, "에이냥"), (2, id_b, "비냥")]
            assert (entries[0]["games"], entries[0]["wins"], entries[1]["losses"]) == (5, 5, 5)
            assert entries[0]["rating"] > 1000 > entries[1]["rating"]

        def test_실패_쪽_번호가_숫자가_아니면_INVALID_INPUT(self, app_env):
            response = app_env.http.get("/api/rankings?page=abc")

            assert response.status_code == 400
            assert response.get_json()["code"] == "INVALID_INPUT"

    class TestProfile:
        def test_성공_레이팅_전적_최근_대국_봇_전적을_보여준다(self, app_env):
            token_a, id_a = create_guest(app_env, "방장냥")
            token_b, _ = create_guest(app_env, "손님냥")
            host, guest = (token_a, connect(app_env, token_a)), (token_b, connect(app_env, token_b))
            play_invite(app_env, host, guest, loser="guest")

            response = app_env.http.get(f"/api/players/{id_a}")

            assert response.status_code == 200
            body = response.get_json()
            assert (body["id"], body["nickname"], body["kind"]) == (id_a, "방장냥", "GUEST")
            assert (body["rating"], body["games"], body["wins"], body["ranked"]) == (1016, 1, 1, False)
            [recent] = body["recentGames"]
            assert (recent["opponentNickname"], recent["result"], recent["mode"]) == ("손님냥", "WIN", "INVITE")
            assert (recent["ratingBefore"], recent["ratingAfter"]) == (1000, 1016)
            assert [r["difficulty"] for r in body["botRecords"]] == ["EASY", "NORMAL", "HARD"]

        def test_실패_없는_플레이어면_404(self, app_env):
            response = app_env.http.get("/api/players/nobody")

            assert response.status_code == 404
            assert response.get_json()["code"] == "PLAYER_NOT_FOUND"

        def test_성공_내_정보_경로는_프로필로_가로채이지_않는다(self, app_env):
            token, _ = create_guest(app_env, "냥냥이")

            response = app_env.http.get("/api/players/me", headers={"Authorization": f"Bearer {token}"})

            assert response.status_code == 200
            assert "token" in response.get_json()
