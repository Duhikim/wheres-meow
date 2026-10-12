import random

import pytest

from fakes import FakeClock
from wheresmeow.game.domain.errors import AlreadyInGame
from wheresmeow.room.adapter.outbound.memory.in_memory_room_store import InMemoryRoomStore
from wheresmeow.room.application.port.outbound import PlayerProfile
from wheresmeow.room.application.service.room_service import RoomService
from wheresmeow.room.domain.room import (
    ROOM_CODE_ALPHABET,
    ROOM_CODE_LENGTH,
    ROOM_TTL_MS,
    NotRoomHost,
    RoomExpired,
    RoomFull,
    RoomNotFound,
    RoomStatus,
    generate_room_code,
)
from wheresmeow.shared.errors import DomainError


class FakePlayerDirectory:
    def profile(self, player_id: str) -> PlayerProfile:
        if player_id == "ghost":
            raise DomainError("없는 플레이어")
        return PlayerProfile(player_id, f"닉-{player_id}", 16, 17)


class FakeGameStarter:
    def __init__(self) -> None:
        self.started: list[tuple[str, str]] = []
        self.fail_with: Exception | None = None

    def start_invite_game(self, host: PlayerProfile, guest: PlayerProfile) -> str:
        if self.fail_with:
            raise self.fail_with
        self.started.append((host.player_id, guest.player_id))
        return "game-1"


@pytest.fixture
def env():
    clock = FakeClock(now_ms=0)
    starter = FakeGameStarter()
    codes = iter(["AAAAAA", "AAAAAA", "BBBBBB"])
    service = RoomService(
        InMemoryRoomStore(), FakePlayerDirectory(), starter, clock, code_factory=lambda: next(codes)
    )
    return service, starter, clock


class TestGenerateRoomCode:
    class TestGenerate:
        def test_성공_혼동되는_문자_없이_6자리를_만든다(self):
            code = generate_room_code(random.Random(1))

            assert len(code) == ROOM_CODE_LENGTH
            assert set(code) <= set(ROOM_CODE_ALPHABET)
            assert not set(code) & set("0O1I")


class TestRoomService:
    class TestCreateRoom:
        def test_성공_이미_쓰는_코드는_건너뛴다(self, env):
            service, *_ = env
            first = service.create_room("host")

            second = service.create_room("host2")

            assert (first.code, second.code) == ("AAAAAA", "BBBBBB")
            assert first.status is RoomStatus.WAITING

        def test_실패_없는_플레이어면_거부한다(self, env):
            service, *_ = env

            with pytest.raises(DomainError):
                service.create_room("ghost")

    class TestJoin:
        def test_성공_방장이_들어오면_대기한다(self, env):
            service, starter, _ = env
            room = service.create_room("host")

            outcome = service.join(room.code, "host")

            assert outcome.game_id is None
            assert starter.started == []

        def test_성공_방장이_새로고침해서_다시_들어와도_계속_대기한다(self, env):
            service, starter, _ = env
            room = service.create_room("host")
            service.join(room.code, "host")

            outcome = service.join(room.code, "host")

            assert outcome.game_id is None
            assert room.status is RoomStatus.WAITING
            assert starter.started == []

        def test_성공_상대가_들어오면_방장을_우선권자로_대국을_시작한다(self, env):
            service, starter, _ = env
            room = service.create_room("host")

            outcome = service.join(room.code.lower(), "guest")  # 소문자로 입력해도 찾는다

            assert outcome.game_id == "game-1"
            assert starter.started == [("host", "guest")]
            assert room.status is RoomStatus.STARTED

        def test_실패_대국이_시작된_방에_세_번째_사람이_오면_거부한다(self, env):
            service, *_ = env
            room = service.create_room("host")
            service.join(room.code, "guest")

            with pytest.raises(RoomFull):
                service.join(room.code, "third")

        def test_실패_10분이_지나면_만료된다(self, env):
            service, _, clock = env
            room = service.create_room("host")
            clock.advance(ROOM_TTL_MS)

            with pytest.raises(RoomExpired):
                service.join(room.code, "guest")

        def test_실패_대국_시작이_실패하면_방은_대기_상태로_남는다(self, env):
            service, starter, _ = env
            room = service.create_room("host")
            starter.fail_with = AlreadyInGame()

            with pytest.raises(AlreadyInGame):
                service.join(room.code, "guest")
            assert room.status is RoomStatus.WAITING

        def test_실패_없는_방이면_거부한다(self, env):
            service, *_ = env

            with pytest.raises(RoomNotFound):
                service.join("ZZZZZZ", "guest")

    class TestCancel:
        def test_성공_방장이_취소하면_더_이상_들어올_수_없다(self, env):
            service, *_ = env
            room = service.create_room("host")

            service.cancel(room.code, "host")

            with pytest.raises(RoomExpired):
                service.join(room.code, "guest")

        def test_실패_방장이_아니면_취소할_수_없다(self, env):
            service, *_ = env
            room = service.create_room("host")

            with pytest.raises(NotRoomHost):
                service.cancel(room.code, "guest")
