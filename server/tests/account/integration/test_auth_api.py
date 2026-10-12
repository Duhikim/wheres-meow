from integration_support import connect, create_guest, received

COOKIE = "wm_refresh"


def signup(app_env, username="neko_01", password="password1", nickname="고양이집사"):
    return app_env.http.post("/api/auth/signup", json={"username": username, "password": password, "nickname": nickname})


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def refresh_cookie(response) -> str:
    header = next(h for h in response.headers.getlist("Set-Cookie") if h.startswith(f"{COOKIE}="))
    return header


class TestSignup:
    class TestPost:
        def test_성공_회원을_만들고_액세스_토큰과_httpOnly_리프레시_쿠키를_준다(self, app_env):
            response = signup(app_env)

            assert response.status_code == 201
            body = response.get_json()
            assert body["player"]["kind"] == "MEMBER"
            cookie = refresh_cookie(response)
            assert "HttpOnly" in cookie and "Path=/api/auth" in cookie and "SameSite=Lax" in cookie
            me = app_env.http.get("/api/players/me", headers=auth(body["token"])).get_json()
            assert (me["nickname"], me["kind"]) == ("고양이집사", "MEMBER")

        def test_실패_같은_아이디면_409_USERNAME_TAKEN(self, app_env):
            signup(app_env)

            response = signup(app_env, nickname="다른냥")

            assert (response.status_code, response.get_json()["code"]) == (409, "USERNAME_TAKEN")

        def test_실패_다른_회원의_닉네임이면_409_NICKNAME_TAKEN(self, app_env):
            signup(app_env)

            response = signup(app_env, username="neko_02")

            assert (response.status_code, response.get_json()["code"]) == (409, "NICKNAME_TAKEN")


class TestLogin:
    class TestPost:
        def test_성공_로그인하면_새_토큰과_쿠키를_준다(self, app_env):
            signup(app_env)

            response = app_env.http.post("/api/auth/login", json={"username": "neko_01", "password": "password1"})

            assert response.status_code == 200
            assert response.get_json()["token"]
            assert refresh_cookie(response)

        def test_실패_틀린_비밀번호면_401_INVALID_CREDENTIALS(self, app_env):
            signup(app_env)

            response = app_env.http.post("/api/auth/login", json={"username": "neko_01", "password": "wrong-pass"})

            assert (response.status_code, response.get_json()["code"]) == (401, "INVALID_CREDENTIALS")

        def test_실패_같은_IP에서_분당_10회를_넘으면_429_RATE_LIMITED(self, app_env):
            for _ in range(10):
                app_env.http.post("/api/auth/login", json={"username": "x_user", "password": "wrong-pass"})

            response = app_env.http.post("/api/auth/login", json={"username": "x_user", "password": "wrong-pass"})

            assert (response.status_code, response.get_json()["code"]) == (429, "RATE_LIMITED")


class TestRefreshAndLogout:
    class TestRefresh:
        def test_성공_쿠키로_새_토큰을_받고_예전_쿠키는_다시_못_쓴다(self, app_env):
            signup(app_env)
            old_cookie = app_env.http.get_cookie(COOKIE, path="/api/auth").value

            response = app_env.http.post("/api/auth/refresh")

            assert response.status_code == 200
            assert response.get_json()["player"]["nickname"] == "고양이집사"
            app_env.http.set_cookie(COOKIE, old_cookie, path="/api/auth")
            assert app_env.http.post("/api/auth/refresh").status_code == 401

        def test_실패_쿠키가_없으면_401(self, app_env):
            assert app_env.http.post("/api/auth/refresh").status_code == 401

    class TestLogout:
        def test_성공_로그아웃하면_쿠키를_지우고_리프레시가_안_된다(self, app_env):
            signup(app_env)
            cookie = app_env.http.get_cookie(COOKIE, path="/api/auth").value

            response = app_env.http.post("/api/auth/logout")

            assert response.status_code == 204
            app_env.http.set_cookie(COOKIE, cookie, path="/api/auth")
            assert app_env.http.post("/api/auth/refresh").status_code == 401


class TestNickname:
    class TestPut:
        def test_성공_닉네임을_바꾼다(self, app_env):
            token = signup(app_env).get_json()["token"]

            response = app_env.http.put("/api/players/me/nickname", json={"nickname": "새이름냥"}, headers=auth(token))

            assert (response.status_code, response.get_json()["nickname"]) == (200, "새이름냥")

        def test_실패_다른_회원의_닉네임이면_409(self, app_env):
            signup(app_env)
            token = signup(app_env, username="neko_02", nickname="둘째냥").get_json()["token"]

            response = app_env.http.put("/api/players/me/nickname", json={"nickname": "고양이집사"}, headers=auth(token))

            assert (response.status_code, response.get_json()["code"]) == (409, "NICKNAME_TAKEN")

        def test_성공_게스트도_닉네임을_바꿀_수_있다(self, app_env):
            token, _ = create_guest(app_env, "게스트냥")

            response = app_env.http.put("/api/players/me/nickname", json={"nickname": "새게스트"}, headers=auth(token))

            assert response.get_json()["nickname"] == "새게스트"


class TestOAuth:
    class TestProviders:
        def test_성공_키가_있는_제공자만_알려_준다(self, app_env):
            assert app_env.http.get("/api/auth/providers").get_json() == {"providers": ["kakao"]}

    class TestAuthorize:
        def test_성공_켜진_제공자면_제공자_로그인_화면으로_보낸다(self, app_env):
            response = app_env.http.get("/api/auth/oauth/kakao/authorize")

            assert response.status_code == 302
            assert response.headers["Location"].startswith("https://fake-provider.test/kakao")

        def test_실패_꺼진_제공자면_404_PROVIDER_DISABLED(self, app_env):
            response = app_env.http.get("/api/auth/oauth/google/authorize")

            assert (response.status_code, response.get_json()["code"]) == (404, "PROVIDER_DISABLED")

    class TestCallback:
        def test_성공_처음이면_새_회원으로_만들고_닉네임_설정으로_보낸다(self, app_env):
            response = app_env.http.get("/api/auth/oauth/kakao/callback")

            assert response.status_code == 302
            assert response.headers["Location"] == "/auth/callback?new=1"
            token = app_env.http.post("/api/auth/refresh").get_json()["token"]
            me = app_env.http.get("/api/players/me", headers=auth(token)).get_json()
            assert (me["kind"], me["needsNickname"]) == ("MEMBER", True)

        def test_성공_두_번째는_기존_회원으로_로그인한다(self, app_env):
            app_env.http.get("/api/auth/oauth/kakao/callback")

            response = app_env.http.get("/api/auth/oauth/kakao/callback")

            assert response.headers["Location"] == "/auth/callback?new=0"


class TestMemberSocket:
    class TestConnect:
        def test_성공_회원_액세스_토큰으로_소켓에_붙어_대국을_시작한다(self, app_env):
            member_token = signup(app_env).get_json()["token"]
            guest_token, _ = create_guest(app_env, "게스트냥")
            code = app_env.http.post("/api/rooms", headers=auth(member_token)).get_json()["code"]
            member, guest = connect(app_env, member_token), connect(app_env, guest_token)

            member.emit("room:join", {"code": code})
            guest.emit("room:join", {"code": code})

            [game] = received(member, "game:started")
            assert [s["nickname"] for s in game["seats"]] == ["고양이집사", "게스트냥"]
