from collections.abc import Callable
from dataclasses import dataclass

from flask import Blueprint, Response, jsonify, redirect, request, url_for
from pydantic import BaseModel, ConfigDict

from wheresmeow.account.adapter.inbound.web.account_api import player_payload
from wheresmeow.account.adapter.inbound.web.oauth_client import OAuthClient
from wheresmeow.account.application.service.member_service import REFRESH_TTL_MS, AuthResult, MemberService
from wheresmeow.account.domain.member import ProviderDisabled
from wheresmeow.shared.errors import Unauthorized
from wheresmeow.shared.payload import parse_payload

REFRESH_COOKIE = "wm_refresh"
COOKIE_PATH = "/api/auth"


class SignupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str
    password: str
    nickname: str


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str
    password: str


@dataclass(frozen=True)
class CookiePolicy:
    secure: bool  # 운영(HTTPS)에서만 True. 개발 서버는 http 라서 False 여야 쿠키가 붙는다.


def create_auth_blueprint(
    members: MemberService,
    oauth: OAuthClient,
    cookie: CookiePolicy,
    rate_limit: Callable[[Callable], Callable],
) -> Blueprint:
    blueprint = Blueprint("auth", __name__, url_prefix="/api/auth")

    def respond(result: AuthResult, status: int = 200) -> Response:
        response = jsonify({"token": result.access_token, "player": player_payload(result.player)})
        response.status_code = status
        response.set_cookie(
            REFRESH_COOKIE,
            result.refresh_token,
            max_age=REFRESH_TTL_MS // 1000,
            path=COOKIE_PATH,
            httponly=True,
            secure=cookie.secure,
            samesite="Lax",  # 소셜 로그인 콜백(다른 사이트에서 돌아오는 이동)에도 쿠키가 붙어야 한다
        )
        return response

    @blueprint.post("/signup")
    @rate_limit
    def post_signup():
        body = parse_payload(SignupRequest, request.get_json(silent=True))
        return respond(members.signup(body.username, body.password, body.nickname), 201)

    @blueprint.post("/login")
    @rate_limit
    def post_login():
        body = parse_payload(LoginRequest, request.get_json(silent=True))
        return respond(members.login(body.username, body.password))

    @blueprint.post("/refresh")
    def post_refresh():
        token = request.cookies.get(REFRESH_COOKIE)
        if not token:
            raise Unauthorized("리프레시 쿠키가 없습니다")
        return respond(members.refresh(token))

    @blueprint.post("/logout")
    def post_logout():
        token = request.cookies.get(REFRESH_COOKIE)
        if token:
            members.logout(token)
        response = Response(status=204)
        response.delete_cookie(REFRESH_COOKIE, path=COOKIE_PATH, secure=cookie.secure, samesite="Lax")
        return response

    @blueprint.get("/providers")
    def get_providers():
        return jsonify({"providers": oauth.enabled_providers()})

    def require_enabled(provider: str) -> None:
        if provider not in oauth.enabled_providers():
            raise ProviderDisabled(f"사용할 수 없는 소셜 로그인입니다: {provider}")

    def callback_uri(provider: str) -> str:
        return url_for("auth.get_oauth_callback", provider=provider, _external=True)

    @blueprint.get("/oauth/<provider>/authorize")
    def get_oauth_authorize(provider: str):
        require_enabled(provider)
        return redirect(oauth.authorize_url(provider, callback_uri(provider)))

    @blueprint.get("/oauth/<provider>/callback")
    def get_oauth_callback(provider: str):
        require_enabled(provider)
        result, is_new = members.oauth_login(provider, oauth.fetch_user_id(provider, callback_uri(provider)))
        # 액세스 토큰은 주소에 싣지 않는다. 화면이 리프레시 쿠키로 새 토큰을 받아 간다.
        response = respond(result)
        response.status_code = 302
        response.headers["Location"] = f"/auth/callback?new={int(is_new)}"
        return response

    return blueprint
