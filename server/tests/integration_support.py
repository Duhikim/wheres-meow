"""통합 테스트 공용 도우미. 앱을 가짜 시계·가짜 타이머·고정 배치로 띄운다."""

from dataclasses import dataclass

from flask import Flask
from flask.testing import FlaskClient
from flask_socketio import SocketIO, SocketIOTestClient

from fakes import FakeClock, FakeTurnTimer
from wheresmeow.bootstrap.app_factory import create_app
from wheresmeow.bootstrap.config import AppConfig
from wheresmeow.game.domain.board import FixedMineLayoutGenerator
from wheresmeow.shared.persistence.database import Database

from persistence_support import migrated_database

# 아래쪽 두 줄(y=10,11) 24마리 + (11,9) = 25마리. (0,0) 은 빈 칸이라 연쇄로 열린다.
INTEGRATION_CATS = {(x, y) for y in (10, 11) for x in range(12)} | {(11, 9)}


class QueueScheduler:
    """봇의 '생각하는 시간' 대신 작업을 쌓아 두고 run_all() 로 직접 실행한다."""

    def __init__(self) -> None:
        self.queue = []

    def __call__(self, task) -> None:
        self.queue.append(task)

    def run_all(self) -> None:
        while self.queue:
            self.queue.pop(0)()


class ManualRepeater:
    """1초마다 도는 매칭 틱 대신, 등록된 작업을 tick() 으로 직접 한 번 실행한다."""

    def __init__(self) -> None:
        self.tasks = []

    def __call__(self, task) -> None:
        self.tasks.append(task)

    def tick(self) -> None:
        for task in self.tasks:
            task()


class FakeOAuthClient:
    """소셜 로그인 제공자 흉내. kakao 만 켜져 있고 콜백은 항상 같은 사용자 ID 를 돌려준다."""

    def __init__(self) -> None:
        self.user_id = "kakao-user-1"

    def enabled_providers(self) -> list[str]:
        return ["kakao"]

    def authorize_url(self, provider: str, redirect_uri: str) -> str:
        return f"https://fake-provider.test/{provider}?redirect_uri={redirect_uri}"

    def fetch_user_id(self, provider: str, redirect_uri: str) -> str:
        return self.user_id


@dataclass
class AppEnv:
    app: Flask
    socketio: SocketIO
    http: FlaskClient
    clock: FakeClock
    timer: FakeTurnTimer
    database: Database
    bot_scheduler: QueueScheduler
    match_repeater: ManualRepeater


def build_app_env(database: Database | None = None) -> AppEnv:
    """database 를 넘기면 같은 DB 를 쓰는 새 앱을 만든다(서버 재시작 흉내)."""
    database = database or migrated_database()
    clock = FakeClock(now_ms=0)
    timer = FakeTurnTimer()
    bot_scheduler = QueueScheduler()
    match_repeater = ManualRepeater()
    app, socketio = create_app(
        AppConfig(env="test", secret_key="test-secret", database_url="sqlite://"),
        database=database,
        clock=clock,
        turn_timer=timer,
        layout_generator=FixedMineLayoutGenerator(INTEGRATION_CATS),
        first_seat_chooser=lambda: 0,
        bot_scheduler=bot_scheduler,
        match_repeater=match_repeater,
        oauth_client=FakeOAuthClient(),
    )
    return AppEnv(app, socketio, app.test_client(), clock, timer, database, bot_scheduler, match_repeater)


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
