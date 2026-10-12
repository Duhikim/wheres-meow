"""통합 테스트 공용 도우미. 앱을 가짜 시계·가짜 타이머·고정 배치로 띄운다."""

from dataclasses import dataclass

from flask import Flask
from flask.testing import FlaskClient
from flask_socketio import SocketIO, SocketIOTestClient

from fakes import FakeClock, FakeTurnTimer
from wheresmeow.bootstrap.app_factory import create_app
from wheresmeow.bootstrap.config import AppConfig
from wheresmeow.game.domain.board import FixedMineLayoutGenerator

# 아래쪽 두 줄(y=10,11) 24마리 + (11,9) = 25마리. (0,0) 은 빈 칸이라 연쇄로 열린다.
INTEGRATION_CATS = {(x, y) for y in (10, 11) for x in range(12)} | {(11, 9)}


@dataclass
class AppEnv:
    app: Flask
    socketio: SocketIO
    http: FlaskClient
    clock: FakeClock
    timer: FakeTurnTimer


def build_app_env() -> AppEnv:
    clock = FakeClock(now_ms=0)
    timer = FakeTurnTimer()
    app, socketio = create_app(
        AppConfig(env="test", secret_key="test-secret"),
        clock=clock,
        turn_timer=timer,
        layout_generator=FixedMineLayoutGenerator(INTEGRATION_CATS),
        first_seat_chooser=lambda: 0,
    )
    return AppEnv(app, socketio, app.test_client(), clock, timer)


def create_guest(env: AppEnv, nickname: str) -> tuple[str, str]:
    """(token, player_id) 를 돌려준다."""
    response = env.http.post("/api/guests", json={"nickname": nickname})
    assert response.status_code == 201, response.get_json()
    body = response.get_json()
    return body["token"], body["player"]["id"]


def connect(env: AppEnv, token: str | None) -> SocketIOTestClient:
    return env.socketio.test_client(env.app, auth={"token": token} if token else None)


def received(client: SocketIOTestClient, name: str) -> list[dict]:
    return [event["args"][0] for event in client.get_received() if event["name"] == name]
