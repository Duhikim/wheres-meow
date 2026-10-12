"""소셜 로그인 제공자와 주고받는 HTTP 흐름. 환경 변수에 키가 있는 제공자만 켠다(스펙 4.4)."""

from typing import Protocol

from authlib.integrations.flask_client import OAuth
from flask import Flask

# 제공자별 설정. 사용자 식별자만 쓰고 이메일 등 다른 정보는 받지 않는다.
PROVIDERS = {
    "google": {
        "server_metadata_url": "https://accounts.google.com/.well-known/openid-configuration",
        "client_kwargs": {"scope": "openid"},
    },
    "naver": {
        "authorize_url": "https://nid.naver.com/oauth2.0/authorize",
        "access_token_url": "https://nid.naver.com/oauth2.0/token",
        "client_kwargs": {"token_endpoint_auth_method": "client_secret_post"},
    },
    "kakao": {
        "authorize_url": "https://kauth.kakao.com/oauth/authorize",
        "access_token_url": "https://kauth.kakao.com/oauth/token",
        "client_kwargs": {"token_endpoint_auth_method": "client_secret_post"},
    },
}
PROFILE_URLS = {
    "naver": "https://openapi.naver.com/v1/nid/me",
    "kakao": "https://kapi.kakao.com/v2/user/me",
}


class OAuthClient(Protocol):
    def enabled_providers(self) -> list[str]: ...

    def authorize_url(self, provider: str, redirect_uri: str) -> str:
        """제공자 로그인 화면 주소. 검증용 state 는 세션에 저장한다."""
        ...

    def fetch_user_id(self, provider: str, redirect_uri: str) -> str:
        """콜백 요청에서 인가 코드를 토큰으로 바꾸고 제공자의 사용자 ID 를 돌려준다."""
        ...


class AuthlibOAuthClient:
    def __init__(self, app: Flask, credentials: dict[str, tuple[str, str]]) -> None:
        unknown = set(credentials) - set(PROVIDERS)
        if unknown:
            raise ValueError(f"지원하지 않는 소셜 로그인 제공자입니다: {sorted(unknown)}")
        self._oauth = OAuth(app)
        self._enabled = sorted(credentials)
        for name in self._enabled:
            client_id, client_secret = credentials[name]
            self._oauth.register(name=name, client_id=client_id, client_secret=client_secret, **PROVIDERS[name])

    def enabled_providers(self) -> list[str]:
        return list(self._enabled)

    def authorize_url(self, provider: str, redirect_uri: str) -> str:
        client = self._oauth.create_client(provider)
        data = client.create_authorization_url(redirect_uri)
        client.save_authorize_data(redirect_uri=redirect_uri, **data)
        return data["url"]

    def fetch_user_id(self, provider: str, redirect_uri: str) -> str:
        client = self._oauth.create_client(provider)
        token = client.authorize_access_token()
        if provider == "google":
            return str(token["userinfo"]["sub"])
        profile = client.get(PROFILE_URLS[provider], token=token).json()
        return str(profile["response"]["id"] if provider == "naver" else profile["id"])
