# Where's Meow 1단계(핵심 대국) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 게스트 두 명이 초대 링크로 만나 12×12 판에서 고양이 찾기 대국을 끝까지 둘 수 있는 최소 서비스(서버 + 웹)를 만든다.

**Architecture:** Flask + Flask-SocketIO 단일 프로세스 서버를 헥사고널 구조(도메인별 `domain` · `application` · `adapter`)로 만든다. 진행 중 상태(플레이어, 방, 대국)는 모두 메모리 저장소에 두되 outbound 포트 뒤에 숨긴다. 웹은 React + Vite + TypeScript이며, 서버 이벤트를 `version` 순서로 적용하는 리듀서 하나로 대국 화면을 그린다.

**Tech Stack:** Python 3.12+ (개발 환경 3.14), Flask 3.1.3, Flask-SocketIO 5.7.0, pydantic 2.14.1, itsdangerous 2.2.0, pytest 9.1.1 / Node 26, React 19.3.0, react-router 8.4.0, socket.io-client 4.8.4, Zustand 5.0.15, Vite 8.3.4, Vitest 5.0.3, TypeScript 7.0.2

**Spec:** `docs/superpowers/specs/2026-10-12-wheres-meow-design.md` (12절 구현 단계 중 1단계)

**검증 상태:** 이 계획의 모든 코드는 계획 작성 시점에 임시 폴더에서 실제로 실행했다. 서버 pytest 109건, 웹 Vitest 17건이 통과했고, `tsc --noEmit`과 `vite build`가 성공했으며, Vite 프록시를 거친 두 게스트의 대국(대기 → 시작 → 한 수 → 기권 → 종료)이 동작했다.

## 스펙 대비 구체화한 사항

계획을 쓰며 스펙의 표현을 다음과 같이 구체화했다. 스펙과 다르게 읽히는 부분은 이 목록이 우선한다.

- **포트 파일 구조**: 스펙 3.2의 `port/inbound/`·`port/outbound/` 디렉터리 대신, 도메인마다 `application/port/inbound.py`·`application/port/outbound.py` 파일 하나씩을 둔다. 포트 수가 적어서 파일을 나눌 이유가 없다.
- **턴 타이머**: 스펙의 `GeventTurnTimer` 대신 `BackgroundTurnTimer`를 쓴다. `socketio.start_background_task`와 `socketio.sleep`을 쓰므로 개발·테스트(`threading`)와 운영(`gevent`)에서 같은 코드가 동작한다.
- **대국 잠금**: 스펙의 gevent `Semaphore` 대신 `threading.Lock`을 쓴다. 운영(8단계)에서 gevent monkey patch를 하면 자동으로 gevent 잠금이 된다.
- **이벤트 전송 대상**: 스펙 5.2의 `game:{id}` 룸 대신, 두 참가자 각각의 `player:{id}` 룸으로 보낸다. 같은 플레이어가 탭을 여러 개 열어도 모두 받는다.
- **추가 오류 코드**: `PLAYER_NOT_FOUND`(404), `NOT_ROOM_HOST`(403).
- **추가 소켓 이벤트**: 서버 → 클라이언트 `room:cancelled {code}`.
- **1단계 범위 밖(스펙상 이후 단계)**: `game:sync`와 재접속 복구(2단계), 고양이 스킨·들풀·발자국 화면(3단계, 1단계는 이모지와 단색 칸), gevent 운영 실행(8단계). 클라이언트는 `version`이 건너뛰면 `outOfSync`만 표시한다.

## Global Constraints

- 서비스 이름은 `Where's Meow`, Python 패키지는 `wheresmeow`, 환경 변수 접두사는 `WHERESMEOW_`이다.
- 판은 12×12, 고양이 25마리, 턴 시간 20초(`TURN_MS = 20_000`), 연속 시간 초과 3회면 자동 기권이다.
- 고양이를 찾으면 +1점과 한 번 더, 시간 초과는 -1점과 턴 넘김, 점수는 음수를 허용한다. 25마리를 모두 찾거나 기권하면 끝나며, 동점이면 무승부다.
- 허용 스킨 ID는 `9, 10, 11, 12, 16, 17, 18, 19, 20, 21`, 기본값은 1P 16·2P 17이다.
- 방 코드는 6자리, 알파벳 `ABCDEFGHJKLMNPQRSTUVWXYZ23456789`, 유효 시간 10분이다.
- 닉네임은 앞뒤 공백을 제거한 뒤 2~12자다.
- 고양이 위치는 `game:ended` 페이로드에만 넣는다. 진행 중 페이로드에 판 정보를 넣지 않는다.
- `domain` 패키지는 Flask·SQLAlchemy·pydantic·Socket.IO를 import하지 않는다. 도메인 사이의 호출은 반드시 포트와 어댑터를 거친다.
- 오류 응답 형식은 HTTP·소켓 모두 `{"code": "...", "message": "..."}`이다.
- 테스트 이름: Python은 `test_성공_...`·`test_실패_...`, TypeScript는 `"[성공] ..."`·`"[실패] ..."`. 구조는 클래스(또는 `describe`) → 메서드 → 케이스다.
- 커밋 메시지는 한국어, 형식은 `type: 짧은 설명`이다.
- 운영 환경(`WHERESMEOW_ENV=production`)에서는 서명 키가 필수이고, `WHERESMEOW_TEST_SEED`가 켜져 있으면 시작을 거부한다.

## Review Focus

스펙이 암시하지만 기능 테스트만으로는 놓치기 쉬운 상황이다. 각 항목의 테스트는 해당 태스크에 포함되어 있다.

1. **같은 칸을 거의 동시에 두 번 누름(더블 탭, 중복 전송)**: 한 번만 적용되고 두 번째 요청은 `CELL_ALREADY_OPEN`으로 거부되어야 한다. → Task 5 `test_성공_같은_칸을_동시에_두_번_눌러도_한_번만_적용된다`
2. **서버 재시작으로 브라우저에 저장된 게스트 토큰이 무효가 됨**: 앱이 세션을 지우고 닉네임 입력으로 돌아가야 하며, 401이 아닌 오류로는 세션을 지우면 안 된다. → Task 10 `sessionStore.test.ts`
3. **기권으로 끝난 뒤 이전 턴의 타이머가 만료됨**: 감점 이벤트가 나가면 안 된다. → Task 5 `test_성공_기권으로_끝난_뒤_이전_턴의_만료는_아무것도_발행하지_않는다`
4. **방장이 대기 화면에서 새로고침해 자기 방에 다시 입장**: 대국이 시작되지 않고 계속 대기해야 한다. → Task 7 `test_성공_방장이_새로고침해서_다시_들어와도_계속_대기한다`
5. **같은 플레이어가 탭을 두 개 열어 둠**: 두 탭 모두 대국 이벤트를 받아야 한다. → Task 9 `test_성공_같은_플레이어가_탭을_두_개_열면_두_탭_모두_이벤트를_받는다`

---

## 파일 구조

```
mind-finder/
├── .gitignore                                  (수정: venv, node_modules, dist, __pycache__)
├── server/
│   ├── pyproject.toml
│   ├── src/wheresmeow/
│   │   ├── __main__.py                         개발 서버 진입점
│   │   ├── shared/
│   │   │   ├── errors.py                       DomainError, InvalidInput, Unauthorized
│   │   │   ├── clock.py                        Clock 포트, SystemClock
│   │   │   ├── payload.py                      pydantic 검증 → InvalidInput
│   │   │   └── socket_rooms.py                 player_room()
│   │   ├── game/
│   │   │   ├── domain/board.py                 Board, 배치 생성기
│   │   │   ├── domain/errors.py                대국 도메인 예외
│   │   │   ├── domain/skins.py                 SkinPreference, assign_skins
│   │   │   ├── domain/game.py                  Game, Seat, 이벤트
│   │   │   ├── application/port/inbound.py     GamePlayer, 유스케이스 프로토콜
│   │   │   ├── application/port/outbound.py    GameStore, GameEventPublisher, TurnTimer
│   │   │   ├── application/service/game_service.py
│   │   │   └── adapter/
│   │   │       ├── inbound/socket/game_socket_handlers.py
│   │   │       ├── outbound/memory/in_memory_game_store.py
│   │   │       ├── outbound/socket/payloads.py
│   │   │       ├── outbound/socket/socketio_game_event_publisher.py
│   │   │       └── outbound/timer/background_turn_timer.py
│   │   ├── account/
│   │   │   ├── domain/player.py
│   │   │   ├── application/port/inbound.py, outbound.py
│   │   │   ├── application/service/guest_service.py
│   │   │   └── adapter/
│   │   │       ├── inbound/web/account_api.py
│   │   │       ├── outbound/memory/in_memory_player_store.py
│   │   │       └── outbound/token/signed_token_issuer.py
│   │   ├── room/
│   │   │   ├── domain/room.py
│   │   │   ├── application/port/inbound.py, outbound.py
│   │   │   ├── application/service/room_service.py
│   │   │   └── adapter/
│   │   │       ├── inbound/web/room_api.py
│   │   │       ├── inbound/socket/room_socket_handlers.py
│   │   │       ├── outbound/memory/in_memory_room_store.py
│   │   │       ├── outbound/account/account_player_directory.py
│   │   │       └── outbound/game/game_starter_adapter.py
│   │   └── bootstrap/
│   │       ├── config.py                       AppConfig (환경 변수, 운영 검증)
│   │       ├── identity.py                     HttpIdentity, SocketSessions
│   │       ├── error_handlers.py               HTTP·소켓 오류 변환
│   │       ├── container.py                    어댑터 → 포트 조립
│   │       └── app_factory.py                  create_app()
│   └── tests/                                  src 구조를 따름 + fakes.py, integration_support.py, conftest.py
└── web/
    ├── package.json, vite.config.ts, tsconfig.json, index.html
    ├── scripts/smoke.mjs                       전체 흐름 자동 확인
    └── src/
        ├── main.tsx, App.tsx, styles.css, errorMessages.ts
        ├── api/http.ts
        ├── session/sessionStore.ts (+test)
        ├── socket/socket.ts
        ├── game/types.ts, gameReducer.ts (+test), cellSize.ts (+test), gameStore.ts, hooks.ts
        ├── components/Board.tsx (+test), NicknameForm.tsx
        └── pages/LobbyPage.tsx, JoinRoomPage.tsx, PlayPage.tsx
```

**패키지 초기화 규칙:** `server/src/wheresmeow/`와 `server/tests/` 아래의 모든 디렉터리에 빈 `__init__.py`를 둔다. 각 태스크에서 새 디렉터리를 만들면 그 디렉터리에도 빈 `__init__.py`를 만든다(아래 단계에서는 반복해서 적지 않는다). 다음 명령으로 한 번에 만들 수 있다.

```bash
cd server && find src/wheresmeow tests -type d -not -name __pycache__ -exec sh -c 'touch "$1/__init__.py"' _ {} \;
```

---

### Task 1: 서버 골격과 공통 모듈

**Files:**
- Modify: `.gitignore`
- Create: `server/pyproject.toml`
- Create: `server/src/wheresmeow/shared/errors.py`
- Create: `server/src/wheresmeow/shared/clock.py`
- Create: `server/tests/fakes.py`
- Test: `server/tests/shared/test_errors.py`

**Interfaces:**
- Produces: `DomainError(message: str | None = None)` (속성 `code: str`, `message: str`), `InvalidInput`(code `INVALID_INPUT`), `Unauthorized`(code `UNAUTHORIZED`); `Clock` 프로토콜 `now_ms() -> int`, `SystemClock`; 테스트용 `FakeClock(now_ms=1_000_000)`(`advance(ms)`), `FakeGameEventPublisher`(`started`, `published: list[(game_id, events)]`), `FakeTurnTimer`(`scheduled: list[(game_id, turn_seq, deadline_ms, on_expire)]`, `fire_latest()`).

- [ ] **Step 1: `.gitignore`에 빌드 산출물 추가**

`.gitignore` 끝에 다음 줄을 추가한다.

```
server/.venv/
__pycache__/
*.egg-info/
web/node_modules/
web/dist/
```

- [ ] **Step 2: `server/pyproject.toml` 작성**

```toml
[build-system]
requires = ["setuptools>=75"]
build-backend = "setuptools.build_meta"

[project]
name = "wheresmeow"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "flask==3.1.3",
    "flask-socketio==5.7.0",
    "simple-websocket==1.1.0",
    "gevent==26.9.0",
    "gevent-websocket==0.10.1",
    "pydantic==2.14.1",
    "itsdangerous==2.2.0",
]

[project.optional-dependencies]
dev = ["pytest==9.1.1"]

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src", "tests"]
addopts = "-q"
```

- [ ] **Step 3: 가상 환경을 만들고 의존성을 설치**

`src/` 디렉터리가 없으면 editable 설치가 `Failed to build ... when getting requirements to build editable`로 실패한다. 패키지 디렉터리를 먼저 만든다.

Run: `mkdir -p server/src/wheresmeow && touch server/src/wheresmeow/__init__.py`

Run: `cd server && python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"`
Expected: `Successfully installed ... flask-3.1.3 flask-socketio-5.7.0 ... pytest-9.1.1 ...`

- [ ] **Step 4: 실패하는 테스트 작성**

`server/tests/shared/test_errors.py`:

```python
from wheresmeow.shared.errors import DomainError, InvalidInput, Unauthorized


class TestDomainError:
    class TestInit:
        def test_성공_메시지가_없으면_코드를_메시지로_쓴다(self):
            error = InvalidInput()

            assert error.code == "INVALID_INPUT"
            assert error.message == "INVALID_INPUT"

        def test_성공_메시지를_주면_그대로_보존한다(self):
            error = Unauthorized("토큰이 만료되었습니다")

            assert error.code == "UNAUTHORIZED"
            assert error.message == "토큰이 만료되었습니다"

        def test_성공_기본_코드는_INTERNAL_이다(self):
            assert DomainError().code == "INTERNAL"
```

`server/tests/fakes.py` (이후 태스크들이 함께 쓰는 가짜 어댑터):

```python
"""여러 도메인의 테스트가 공유하는 가짜 어댑터."""

from collections.abc import Callable, Sequence


class FakeClock:
    def __init__(self, now_ms: int = 1_000_000) -> None:
        self._now = now_ms

    def now_ms(self) -> int:
        return self._now

    def advance(self, ms: int) -> None:
        self._now += ms


class FakeGameEventPublisher:
    def __init__(self) -> None:
        self.started: list = []
        self.published: list = []  # (game_id, events)

    def game_started(self, game) -> None:
        self.started.append(game)

    def publish(self, game, events: Sequence) -> None:
        self.published.append((game.id, list(events)))


class FakeTurnTimer:
    """예약만 기록하고, fire_latest() 를 호출해야 만료가 일어난다."""

    def __init__(self) -> None:
        self.scheduled: list[tuple[str, int, int, Callable[[str, int], None]]] = []

    def schedule(self, game_id: str, turn_seq: int, deadline_ms: int, on_expire) -> None:
        self.scheduled.append((game_id, turn_seq, deadline_ms, on_expire))

    def fire_latest(self) -> None:
        game_id, turn_seq, _, on_expire = self.scheduled[-1]
        on_expire(game_id, turn_seq)
```

`server/tests/__init__.py`, `server/tests/shared/__init__.py`를 빈 파일로 만든다.

- [ ] **Step 5: 테스트가 실패하는지 확인**

Run: `cd server && .venv/bin/pytest tests/shared -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'wheresmeow.shared'`

- [ ] **Step 6: 구현**

`server/src/wheresmeow/shared/errors.py`:

```python
"""모든 도메인이 공유하는 예외 기반 클래스."""


class DomainError(Exception):
    """오류 코드가 붙은 도메인 규칙 위반. 하위 클래스는 code 만 바꾼다."""

    code: str = "INTERNAL"

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.code
        super().__init__(self.message)


class InvalidInput(DomainError):
    code = "INVALID_INPUT"


class Unauthorized(DomainError):
    code = "UNAUTHORIZED"
```

`server/src/wheresmeow/shared/clock.py`:

```python
"""현재 시각을 밀리초 epoch 로 제공하는 포트와 구현."""

import time
from typing import Protocol


class Clock(Protocol):
    def now_ms(self) -> int: ...


class SystemClock:
    def now_ms(self) -> int:
        return int(time.time() * 1000)
```

`server/src/wheresmeow/__init__.py`, `server/src/wheresmeow/shared/__init__.py`를 빈 파일로 만든다.

- [ ] **Step 7: 테스트 통과 확인**

Run: `cd server && .venv/bin/pytest tests/shared -v`
Expected: PASS (3 passed)

- [ ] **Step 8: 커밋**

```bash
git add .gitignore server/pyproject.toml server/src server/tests
git commit -m "chore: 서버 골격과 공통 예외·시계 모듈 추가"
```

---

### Task 2: 판(Board)과 고양이 배치 생성기

**Files:**
- Create: `server/src/wheresmeow/game/domain/board.py`
- Test: `server/tests/game/test_board.py`

**Interfaces:**
- Produces: 상수 `BOARD_SIZE = 12`, `CAT_COUNT = 25`; 타입 `Position = tuple[int, int]` (x, y); `MineLayoutGenerator` 프로토콜 `generate(size, cat_count) -> frozenset[Position]`; 구현 `RandomMineLayoutGenerator(rng=None)`, `SeededMineLayoutGenerator(seed)`, `FixedMineLayoutGenerator(cats: set[Position])`; `Board(size, cats)` — `in_bounds(x, y)`, `is_cat(x, y)`, `adjacent_count(x, y)`, `neighbors(x, y)`, 속성 `size`, `cats`.

- [ ] **Step 1: 실패하는 테스트 작성**

`server/tests/game/test_board.py`:

```python
import pytest

from wheresmeow.game.domain.board import (
    BOARD_SIZE,
    CAT_COUNT,
    Board,
    RandomMineLayoutGenerator,
    SeededMineLayoutGenerator,
)


class TestBoard:
    class TestInit:
        def test_실패_판_밖의_고양이가_있으면_거부한다(self):
            with pytest.raises(ValueError):
                Board(3, frozenset({(3, 0)}))

        def test_실패_고양이가_없으면_거부한다(self):
            with pytest.raises(ValueError):
                Board(3, frozenset())

        def test_실패_모든_칸이_고양이면_거부한다(self):
            cats = frozenset((x, y) for x in range(2) for y in range(2))
            with pytest.raises(ValueError):
                Board(2, cats)

    class TestAdjacentCount:
        def test_성공_주변_고양이_수를_센다(self):
            board = Board(3, frozenset({(0, 0), (2, 2)}))

            assert board.adjacent_count(1, 1) == 2
            assert board.adjacent_count(1, 0) == 1
            assert board.adjacent_count(2, 0) == 0

        def test_성공_모서리_칸은_판_밖을_세지_않는다(self):
            board = Board(3, frozenset({(1, 1)}))

            assert board.adjacent_count(0, 0) == 1
            assert len(list(board.neighbors(0, 0))) == 3


class TestRandomMineLayoutGenerator:
    class TestGenerate:
        def test_성공_고양이_25마리를_판_안에_서로_다른_칸에_놓는다(self):
            cats = RandomMineLayoutGenerator().generate(BOARD_SIZE, CAT_COUNT)

            assert len(cats) == CAT_COUNT
            assert all(0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE for x, y in cats)

        def test_성공_같은_시드면_같은_배치를_만든다(self):
            first = SeededMineLayoutGenerator(42).generate(BOARD_SIZE, CAT_COUNT)
            second = SeededMineLayoutGenerator(42).generate(BOARD_SIZE, CAT_COUNT)

            assert first == second
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `cd server && .venv/bin/pytest tests/game/test_board.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'wheresmeow.game'`

- [ ] **Step 3: 구현**

`server/src/wheresmeow/game/domain/board.py`:

```python
"""12x12 판과 고양이(지뢰) 배치."""

import random
from collections.abc import Iterator
from typing import Protocol

BOARD_SIZE = 12
CAT_COUNT = 25

Position = tuple[int, int]  # (x, y)


class MineLayoutGenerator(Protocol):
    def generate(self, size: int, cat_count: int) -> frozenset[Position]: ...


class RandomMineLayoutGenerator:
    """운영용. 기본값은 OS 난수(secrets 와 같은 출처)를 쓴다."""

    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng or random.SystemRandom()

    def generate(self, size: int, cat_count: int) -> frozenset[Position]:
        cells = [(x, y) for y in range(size) for x in range(size)]
        return frozenset(self._rng.sample(cells, cat_count))


class SeededMineLayoutGenerator(RandomMineLayoutGenerator):
    """테스트·E2E 용. 같은 시드면 항상 같은 배치를 만든다."""

    def __init__(self, seed: int) -> None:
        super().__init__(random.Random(seed))


class FixedMineLayoutGenerator:
    """테스트용. 미리 정한 배치를 그대로 돌려준다."""

    def __init__(self, cats: set[Position]) -> None:
        self._cats = frozenset(cats)

    def generate(self, size: int, cat_count: int) -> frozenset[Position]:
        return self._cats


class Board:
    def __init__(self, size: int, cats: frozenset[Position]) -> None:
        if size <= 0:
            raise ValueError(f"판 크기는 양수여야 합니다: {size}")
        if not cats or len(cats) >= size * size:
            raise ValueError(f"고양이 수가 올바르지 않습니다: {len(cats)}")
        outside = [p for p in cats if not (0 <= p[0] < size and 0 <= p[1] < size)]
        if outside:
            raise ValueError(f"판 밖의 고양이 위치가 있습니다: {outside}")
        self.size = size
        self.cats = cats
        self._counts = {
            (x, y): sum(1 for n in self.neighbors(x, y) if n in cats)
            for y in range(size)
            for x in range(size)
        }

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.size and 0 <= y < self.size

    def is_cat(self, x: int, y: int) -> bool:
        return (x, y) in self.cats

    def adjacent_count(self, x: int, y: int) -> int:
        return self._counts[(x, y)]

    def neighbors(self, x: int, y: int) -> Iterator[Position]:
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if (dx or dy) and self.in_bounds(x + dx, y + dy):
                    yield (x + dx, y + dy)
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `cd server && .venv/bin/pytest tests/game/test_board.py -v`
Expected: PASS (7 passed)

- [ ] **Step 5: 커밋**

```bash
git add server/src/wheresmeow/game server/tests/game
git commit -m "feat: 판과 고양이 배치 생성기 추가"
```

---

### Task 3: 대국 도메인 예외와 스킨 배정 규칙

**Files:**
- Create: `server/src/wheresmeow/game/domain/errors.py`
- Create: `server/src/wheresmeow/game/domain/skins.py`
- Test: `server/tests/game/test_skins.py`

**Interfaces:**
- Consumes: `DomainError` (Task 1)
- Produces: 예외 `NotYourTurn`, `CellAlreadyOpen`, `OutOfBoard`, `GameFinished`, `GameNotFound`, `NotAParticipant`, `AlreadyInGame`, `InvalidSkin` (각 code는 클래스 이름의 SNAKE_CASE); `ALLOWED_SKINS`, `DEFAULT_SKIN_1P = 16`, `DEFAULT_SKIN_2P = 17`; `SkinPreference(skin_1p=16, skin_2p=17)` (생성 시 검증); `assign_skins(priority, other) -> tuple[int, int]`.

- [ ] **Step 1: 실패하는 테스트 작성**

`server/tests/game/test_skins.py`:

```python
import pytest

from wheresmeow.game.domain.errors import InvalidSkin
from wheresmeow.game.domain.skins import SkinPreference, assign_skins


class TestSkinPreference:
    class TestInit:
        def test_성공_기본값은_16과_17이다(self):
            pref = SkinPreference()

            assert (pref.skin_1p, pref.skin_2p) == (16, 17)

        def test_실패_허용하지_않는_스킨이면_거부한다(self):
            with pytest.raises(InvalidSkin):
                SkinPreference(13, 16)

        def test_실패_1P와_2P가_같으면_거부한다(self):
            with pytest.raises(InvalidSkin):
                SkinPreference(9, 9)


class TestAssignSkins:
    class TestAssign:
        def test_성공_1P가_다르면_둘_다_1P를_쓴다(self):
            assert assign_skins(SkinPreference(16, 17), SkinPreference(18, 19)) == (16, 18)

        def test_성공_1P가_겹치면_우선권_없는_쪽이_2P를_쓴다(self):
            assert assign_skins(SkinPreference(16, 17), SkinPreference(16, 20)) == (16, 20)

        def test_성공_상대의_2P가_우선권자의_1P와_같아도_겹치지_않는다(self):
            # 상대 1P(17) 가 우선권자 1P(16) 와 다르므로 상대는 1P 를 쓴다
            assert assign_skins(SkinPreference(16, 17), SkinPreference(17, 16)) == (16, 17)
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `cd server && .venv/bin/pytest tests/game/test_skins.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'wheresmeow.game.domain.errors'`

- [ ] **Step 3: 구현**

`server/src/wheresmeow/game/domain/errors.py`:

```python
from wheresmeow.shared.errors import DomainError


class NotYourTurn(DomainError):
    code = "NOT_YOUR_TURN"


class CellAlreadyOpen(DomainError):
    code = "CELL_ALREADY_OPEN"


class OutOfBoard(DomainError):
    code = "OUT_OF_BOARD"


class GameFinished(DomainError):
    code = "GAME_FINISHED"


class GameNotFound(DomainError):
    code = "GAME_NOT_FOUND"


class NotAParticipant(DomainError):
    code = "NOT_A_PARTICIPANT"


class AlreadyInGame(DomainError):
    code = "ALREADY_IN_GAME"


class InvalidSkin(DomainError):
    code = "INVALID_SKIN"
```

`server/src/wheresmeow/game/domain/skins.py`:

```python
"""고양이 스킨 목록과 대국 시 스킨 배정 규칙."""

from dataclasses import dataclass

from wheresmeow.game.domain.errors import InvalidSkin

ALLOWED_SKINS = frozenset({9, 10, 11, 12, 16, 17, 18, 19, 20, 21})
DEFAULT_SKIN_1P = 16
DEFAULT_SKIN_2P = 17


@dataclass(frozen=True)
class SkinPreference:
    skin_1p: int = DEFAULT_SKIN_1P
    skin_2p: int = DEFAULT_SKIN_2P

    def __post_init__(self) -> None:
        if self.skin_1p not in ALLOWED_SKINS or self.skin_2p not in ALLOWED_SKINS:
            raise InvalidSkin(f"허용하지 않는 스킨입니다: {self.skin_1p}, {self.skin_2p}")
        if self.skin_1p == self.skin_2p:
            raise InvalidSkin("1P 와 2P 스킨은 서로 달라야 합니다")


def assign_skins(priority: SkinPreference, other: SkinPreference) -> tuple[int, int]:
    """우선권자는 항상 1P. 상대는 1P 가 겹칠 때만 2P 를 쓴다.

    1P 와 2P 가 항상 다르므로 결과 두 값은 반드시 서로 다르다.
    """
    other_skin = other.skin_2p if other.skin_1p == priority.skin_1p else other.skin_1p
    return priority.skin_1p, other_skin
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `cd server && .venv/bin/pytest tests/game/test_skins.py -v`
Expected: PASS (6 passed)

- [ ] **Step 5: 커밋**

```bash
git add server/src/wheresmeow/game/domain server/tests/game/test_skins.py
git commit -m "feat: 대국 도메인 예외와 스킨 배정 규칙 추가"
```

---

### Task 4: 대국 엔티티(Game)

**Files:**
- Create: `server/src/wheresmeow/game/domain/game.py`
- Test: `server/tests/game/test_game.py`

**Interfaces:**
- Consumes: `Board`, `Position` (Task 2); 예외들 (Task 3)
- Produces: `TURN_MS = 20_000`, `MAX_CONSECUTIVE_TIMEOUTS = 3`; `GameMode`(INVITE·MATCH·BOT), `GameStatus`(IN_PROGRESS·FINISHED), `EndReason`(ALL_FOUND·FORFEIT·AUTO_FORFEIT); `Seat(player_id, nickname, skin, score=0, consecutive_timeouts=0)`; `OpenedCell(x, y, number: int | None, found_by: int | None)`; 이벤트 `CellsRevealed(version, seat, cells, scores, current_seat, turn_deadline_ms)`, `TurnTimedOut(version, seat, scores, current_seat, turn_deadline_ms)`, `GameEnded(version, reason, winner, scores, cats)`, `GameEvent` 유니온; `Game(id, mode, board, seats, first_seat, started_at_ms)` — `reveal(player_id, x, y, now_ms)`, `timeout(turn_seq, now_ms)`, `forfeit(player_id, now_ms)` 모두 `list[GameEvent]` 반환, `seat_of(player_id)`, `is_participant(player_id)`, 속성 `scores`, `found_count`, `status`, `version`, `turn_seq`, `current_seat`, `turn_deadline_ms`, `opened`, `winner`, `end_reason`, `moves`.

- [ ] **Step 1: 실패하는 테스트 작성**

판은 4×4, 고양이는 (0,0) (3,0) (3,3)이다. 숫자와 연쇄 열기 결과를 손으로 계산할 수 있도록 테스트 파일 맨 위 주석에 판을 그려 두었다.

`server/tests/game/test_game.py`:

```python
"""Game 엔티티 테스트.

4x4 판, 고양이 위치 (0,0) (3,0) (3,3). 각 칸의 숫자는 다음과 같다(C = 고양이).

    y=0:  C 1 1 C
    y=1:  1 1 1 1
    y=2:  0 0 1 1
    y=3:  0 0 1 C
"""

import pytest

from wheresmeow.game.domain.board import Board
from wheresmeow.game.domain.errors import (
    CellAlreadyOpen,
    GameFinished,
    NotAParticipant,
    NotYourTurn,
    OutOfBoard,
)
from wheresmeow.game.domain.game import (
    TURN_MS,
    CellsRevealed,
    EndReason,
    Game,
    GameEnded,
    GameMode,
    GameStatus,
    Seat,
    TurnTimedOut,
)

CATS = frozenset({(0, 0), (3, 0), (3, 3)})
A, B = "player-a", "player-b"


def make_game(first_seat: int = 0, now_ms: int = 0) -> Game:
    seats = (Seat(A, "에이", 16), Seat(B, "비", 17))
    return Game("g1", GameMode.INVITE, Board(4, CATS), seats, first_seat, now_ms)


class TestGame:
    class TestInit:
        def test_성공_선공_좌석의_턴으로_시작한다(self):
            game = make_game(first_seat=1, now_ms=500)

            assert game.current_seat == 1
            assert game.turn_seq == 1
            assert game.turn_deadline_ms == 500 + TURN_MS
            assert game.version == 0

        def test_실패_같은_플레이어가_두_좌석에_앉으면_거부한다(self):
            with pytest.raises(ValueError):
                Game("g", GameMode.INVITE, Board(4, CATS), (Seat(A, "a", 16), Seat(A, "a", 17)), 0, 0)

    class TestReveal:
        def test_성공_고양이를_찾으면_1점을_얻고_한번_더_둔다(self):
            game = make_game()

            events = game.reveal(A, 0, 0, now_ms=1000)

            assert game.scores == (1, 0)
            assert game.current_seat == 0
            assert game.turn_seq == 2
            assert game.turn_deadline_ms == 1000 + TURN_MS
            [event] = events
            assert isinstance(event, CellsRevealed)
            assert event.cells[0].found_by == 0
            assert event.cells[0].number is None

        def test_성공_숫자_칸이면_그_칸만_열고_턴이_넘어간다(self):
            game = make_game()

            [event] = game.reveal(A, 1, 0, now_ms=0)

            assert [(c.x, c.y, c.number) for c in event.cells] == [(1, 0, 1)]
            assert game.current_seat == 1
            assert event.current_seat == 1

        def test_성공_빈_칸이면_연결된_영역을_열되_고양이는_열지_않는다(self):
            game = make_game()

            [event] = game.reveal(A, 0, 3, now_ms=0)

            opened = {(c.x, c.y) for c in event.cells}
            assert opened == {(0, 3), (1, 3), (0, 2), (1, 2), (2, 3), (2, 2), (0, 1), (1, 1), (2, 1)}
            assert opened.isdisjoint(CATS)
            assert game.current_seat == 1

        def test_성공_정상_수를_두면_연속_시간_초과_횟수가_초기화된다(self):
            game = make_game()
            game.timeout(game.turn_seq, now_ms=0)  # A 초과 → B 차례
            game.reveal(B, 1, 0, now_ms=0)  # B 숫자 → A 차례

            game.reveal(A, 2, 0, now_ms=0)

            assert game.seats[0].consecutive_timeouts == 0

        def test_성공_마지막_고양이를_찾으면_점수가_높은_쪽이_이기고_끝난다(self):
            game = make_game()
            game.reveal(A, 0, 0, now_ms=0)
            game.reveal(A, 3, 0, now_ms=0)

            events = game.reveal(A, 3, 3, now_ms=0)

            revealed, ended = events
            assert isinstance(revealed, CellsRevealed)
            assert revealed.turn_deadline_ms is None
            assert isinstance(ended, GameEnded)
            assert ended.reason is EndReason.ALL_FOUND
            assert ended.winner == 0
            assert ended.scores == (3, 0)
            assert set(ended.cats) == CATS
            assert game.status is GameStatus.FINISHED

        def test_성공_마지막_고양이를_찾았을_때_동점이면_무승부다(self):
            game = make_game()
            game.reveal(A, 0, 0, now_ms=0)  # A 1:0
            game.timeout(game.turn_seq, now_ms=0)  # A 0:0 → B 차례
            game.reveal(B, 3, 0, now_ms=0)  # B 0:1
            game.reveal(B, 2, 0, now_ms=0)  # B 숫자 → A 차례

            _, ended = game.reveal(A, 3, 3, now_ms=0)  # A 1:1

            assert ended.winner is None
            assert ended.scores == (1, 1)

        def test_성공_이벤트마다_version이_1씩_증가한다(self):
            game = make_game()
            game.reveal(A, 0, 0, now_ms=0)
            game.reveal(A, 3, 0, now_ms=0)

            revealed, ended = game.reveal(A, 3, 3, now_ms=0)

            assert (revealed.version, ended.version) == (3, 4)
            assert game.version == 4

        def test_실패_자기_차례가_아니면_거부한다(self):
            with pytest.raises(NotYourTurn):
                make_game().reveal(B, 1, 0, now_ms=0)

        def test_실패_이미_열린_칸이면_거부한다(self):
            game = make_game()
            game.reveal(A, 0, 0, now_ms=0)

            with pytest.raises(CellAlreadyOpen):
                game.reveal(A, 0, 0, now_ms=0)

        def test_실패_판_밖이면_거부한다(self):
            with pytest.raises(OutOfBoard):
                make_game().reveal(A, 4, 0, now_ms=0)

        def test_실패_참가자가_아니면_거부한다(self):
            with pytest.raises(NotAParticipant):
                make_game().reveal("stranger", 1, 0, now_ms=0)

        def test_실패_끝난_대국이면_거부한다(self):
            game = make_game()
            game.forfeit(B, now_ms=0)

            with pytest.raises(GameFinished):
                game.reveal(A, 1, 0, now_ms=0)

    class TestTimeout:
        def test_성공_1점을_잃고_턴이_넘어간다(self):
            game = make_game()

            [event] = game.timeout(game.turn_seq, now_ms=2000)

            assert isinstance(event, TurnTimedOut)
            assert event.seat == 0
            assert event.scores == (-1, 0)
            assert event.current_seat == 1
            assert event.turn_deadline_ms == 2000 + TURN_MS

        def test_성공_점수는_음수가_될_수_있다(self):
            game = make_game()
            game.timeout(game.turn_seq, now_ms=0)
            game.timeout(game.turn_seq, now_ms=0)
            game.timeout(game.turn_seq, now_ms=0)

            assert game.scores == (-2, -1)

        def test_성공_지나간_턴의_타이머는_무시한다(self):
            game = make_game()
            stale = game.turn_seq
            game.reveal(A, 1, 0, now_ms=0)

            assert game.timeout(stale, now_ms=0) == []
            assert game.scores == (0, 0)

        def test_성공_같은_플레이어가_3회_연속_초과하면_자동_기권패다(self):
            game = make_game()
            for _ in range(4):  # A, B, A, B 각각 초과
                game.timeout(game.turn_seq, now_ms=0)

            timed_out, ended = game.timeout(game.turn_seq, now_ms=0)  # A 세 번째

            assert timed_out.seat == 0
            assert timed_out.turn_deadline_ms is None
            assert ended.reason is EndReason.AUTO_FORFEIT
            assert ended.winner == 1

    class TestForfeit:
        def test_성공_점수와_관계없이_기권한_쪽이_진다(self):
            game = make_game()
            game.reveal(A, 0, 0, now_ms=0)  # A 1:0

            [ended] = game.forfeit(A, now_ms=0)

            assert ended.reason is EndReason.FORFEIT
            assert ended.winner == 1

        def test_성공_자기_차례가_아니어도_기권할_수_있다(self):
            [ended] = make_game().forfeit(B, now_ms=0)

            assert ended.winner == 0

        def test_실패_끝난_대국이면_거부한다(self):
            game = make_game()
            game.forfeit(A, now_ms=0)

            with pytest.raises(GameFinished):
                game.forfeit(B, now_ms=0)
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `cd server && .venv/bin/pytest tests/game/test_game.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'wheresmeow.game.domain.game'`

- [ ] **Step 3: 구현**

핵심 규칙: 고양이를 찾으면 같은 좌석으로 새 턴을 시작하고(`_start_turn(seat)`), 숫자·빈 칸이면 상대 좌석으로 넘긴다. 이벤트를 만들 때마다 `version`을 1 올린다. 끝날 때(`_finish`)는 `turn_deadline_ms`를 `None`으로 만든 뒤 이벤트를 만든다. `timeout`은 전달받은 `turn_seq`가 현재 값과 다르거나 대국이 끝났으면 빈 목록을 돌려준다.

`server/src/wheresmeow/game/domain/game.py`:

```python
"""대국 엔티티. 규칙 판정은 모두 여기서 하며 Flask·DB 를 모른다."""

from collections import deque
from dataclasses import dataclass, field
from enum import StrEnum

from wheresmeow.game.domain.board import Board, Position
from wheresmeow.game.domain.errors import (
    CellAlreadyOpen,
    GameFinished,
    NotAParticipant,
    NotYourTurn,
    OutOfBoard,
)

TURN_MS = 20_000
MAX_CONSECUTIVE_TIMEOUTS = 3


class GameMode(StrEnum):
    INVITE = "INVITE"
    MATCH = "MATCH"
    BOT = "BOT"


class GameStatus(StrEnum):
    IN_PROGRESS = "IN_PROGRESS"
    FINISHED = "FINISHED"


class EndReason(StrEnum):
    ALL_FOUND = "ALL_FOUND"
    FORFEIT = "FORFEIT"
    AUTO_FORFEIT = "AUTO_FORFEIT"


@dataclass
class Seat:
    player_id: str
    nickname: str
    skin: int
    score: int = 0
    consecutive_timeouts: int = 0


@dataclass(frozen=True)
class OpenedCell:
    x: int
    y: int
    number: int | None  # 숫자·빈 칸이면 주변 고양이 수, 고양이 칸이면 None
    found_by: int | None  # 고양이 칸이면 찾은 좌석(0 또는 1)


@dataclass(frozen=True)
class CellsRevealed:
    version: int
    seat: int
    cells: tuple[OpenedCell, ...]
    scores: tuple[int, int]
    current_seat: int
    turn_deadline_ms: int | None


@dataclass(frozen=True)
class TurnTimedOut:
    version: int
    seat: int
    scores: tuple[int, int]
    current_seat: int
    turn_deadline_ms: int | None


@dataclass(frozen=True)
class GameEnded:
    version: int
    reason: EndReason
    winner: int | None  # None 이면 무승부
    scores: tuple[int, int]
    cats: tuple[Position, ...]


GameEvent = CellsRevealed | TurnTimedOut | GameEnded


@dataclass
class Game:
    id: str
    mode: GameMode
    board: Board
    seats: tuple[Seat, Seat]
    first_seat: int
    started_at_ms: int
    status: GameStatus = GameStatus.IN_PROGRESS
    version: int = 0
    turn_seq: int = 0
    current_seat: int = 0
    turn_deadline_ms: int | None = None
    end_reason: EndReason | None = None
    winner: int | None = None
    opened: dict[Position, OpenedCell] = field(default_factory=dict)
    moves: list[dict] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.first_seat not in (0, 1):
            raise ValueError(f"선공 좌석은 0 또는 1 이어야 합니다: {self.first_seat}")
        if self.seats[0].player_id == self.seats[1].player_id:
            raise ValueError("같은 플레이어가 두 좌석에 앉을 수 없습니다")
        self._start_turn(self.first_seat, self.started_at_ms)

    # ---- 조회 ----

    @property
    def scores(self) -> tuple[int, int]:
        return self.seats[0].score, self.seats[1].score

    @property
    def found_count(self) -> int:
        return sum(1 for cell in self.opened.values() if cell.found_by is not None)

    def seat_of(self, player_id: str) -> int:
        for index, seat in enumerate(self.seats):
            if seat.player_id == player_id:
                return index
        raise NotAParticipant(f"대국 참가자가 아닙니다: {player_id}")

    def is_participant(self, player_id: str) -> bool:
        return any(seat.player_id == player_id for seat in self.seats)

    # ---- 동작 ----

    def reveal(self, player_id: str, x: int, y: int, now_ms: int) -> list[GameEvent]:
        self._ensure_in_progress()
        seat = self.seat_of(player_id)
        if seat != self.current_seat:
            raise NotYourTurn()
        if not self.board.in_bounds(x, y):
            raise OutOfBoard(f"판 밖의 칸입니다: ({x}, {y})")
        if (x, y) in self.opened:
            raise CellAlreadyOpen(f"이미 열린 칸입니다: ({x}, {y})")

        mover = self.seats[seat]
        mover.consecutive_timeouts = 0
        self.moves.append({"type": "reveal", "seat": seat, "x": x, "y": y, "at": now_ms})

        if self.board.is_cat(x, y):
            cell = OpenedCell(x, y, None, seat)
            self.opened[(x, y)] = cell
            mover.score += 1
            if self.found_count == len(self.board.cats):
                self._finish(EndReason.ALL_FOUND, self._leader())
                return [self._revealed(seat, (cell,)), self._ended()]
            self._start_turn(seat, now_ms)  # 고양이를 찾으면 한 번 더
            return [self._revealed(seat, (cell,))]

        cells = self._flood_open(x, y)
        self._start_turn(1 - seat, now_ms)
        return [self._revealed(seat, cells)]

    def timeout(self, turn_seq: int, now_ms: int) -> list[GameEvent]:
        """타이머 만료. 이미 지나간 턴의 타이머면 아무것도 하지 않는다."""
        if self.status is not GameStatus.IN_PROGRESS or turn_seq != self.turn_seq:
            return []
        seat = self.current_seat
        loser = self.seats[seat]
        loser.score -= 1
        loser.consecutive_timeouts += 1
        self.moves.append({"type": "timeout", "seat": seat, "at": now_ms})

        if loser.consecutive_timeouts >= MAX_CONSECUTIVE_TIMEOUTS:
            self._finish(EndReason.AUTO_FORFEIT, 1 - seat)
            return [self._timed_out(seat), self._ended()]
        self._start_turn(1 - seat, now_ms)
        return [self._timed_out(seat)]

    def forfeit(self, player_id: str, now_ms: int) -> list[GameEvent]:
        self._ensure_in_progress()
        seat = self.seat_of(player_id)
        self.moves.append({"type": "forfeit", "seat": seat, "at": now_ms})
        self._finish(EndReason.FORFEIT, 1 - seat)
        return [self._ended()]

    # ---- 내부 ----

    def _ensure_in_progress(self) -> None:
        if self.status is not GameStatus.IN_PROGRESS:
            raise GameFinished()

    def _start_turn(self, seat: int, now_ms: int) -> None:
        self.current_seat = seat
        self.turn_seq += 1
        self.turn_deadline_ms = now_ms + TURN_MS

    def _finish(self, reason: EndReason, winner: int | None) -> None:
        self.status = GameStatus.FINISHED
        self.end_reason = reason
        self.winner = winner
        self.turn_deadline_ms = None

    def _leader(self) -> int | None:
        first, second = self.scores
        if first == second:
            return None
        return 0 if first > second else 1

    def _flood_open(self, x: int, y: int) -> tuple[OpenedCell, ...]:
        opened: list[OpenedCell] = []
        queue: deque[Position] = deque([(x, y)])
        while queue:
            position = queue.popleft()
            if position in self.opened or self.board.is_cat(*position):
                continue
            number = self.board.adjacent_count(*position)
            cell = OpenedCell(position[0], position[1], number, None)
            self.opened[position] = cell
            opened.append(cell)
            if number == 0:
                queue.extend(n for n in self.board.neighbors(*position) if n not in self.opened)
        return tuple(opened)

    def _next_version(self) -> int:
        self.version += 1
        return self.version

    def _revealed(self, seat: int, cells: tuple[OpenedCell, ...]) -> CellsRevealed:
        return CellsRevealed(
            self._next_version(), seat, cells, self.scores, self.current_seat, self.turn_deadline_ms
        )

    def _timed_out(self, seat: int) -> TurnTimedOut:
        return TurnTimedOut(
            self._next_version(), seat, self.scores, self.current_seat, self.turn_deadline_ms
        )

    def _ended(self) -> GameEnded:
        assert self.end_reason is not None
        return GameEnded(
            self._next_version(), self.end_reason, self.winner, self.scores, tuple(sorted(self.board.cats))
        )
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `cd server && .venv/bin/pytest tests/game/test_game.py -v`
Expected: PASS (21 passed)

- [ ] **Step 5: 커밋**

```bash
git add server/src/wheresmeow/game/domain/game.py server/tests/game/test_game.py
git commit -m "feat: 대국 엔티티와 열기·시간 초과·기권 규칙 구현"
```

---

### Task 5: 대국 유스케이스(GameService)와 메모리 저장소

**Files:**
- Create: `server/src/wheresmeow/game/application/port/inbound.py`
- Create: `server/src/wheresmeow/game/application/port/outbound.py`
- Create: `server/src/wheresmeow/game/application/service/game_service.py`
- Create: `server/src/wheresmeow/game/adapter/outbound/memory/in_memory_game_store.py`
- Test: `server/tests/game/test_game_service.py`

**Interfaces:**
- Consumes: `Board`, `MineLayoutGenerator`, `BOARD_SIZE`, `CAT_COUNT` (Task 2); `SkinPreference`, `assign_skins`, `AlreadyInGame`, `GameNotFound` (Task 3); `Game`, `Seat`, `GameMode`, `GameStatus`, `GameEvent` (Task 4); `Clock` (Task 1); 테스트에서 `FakeClock`, `FakeGameEventPublisher`, `FakeTurnTimer` (Task 1)
- Produces: `GamePlayer(player_id, nickname, skins: SkinPreference)`; 프로토콜 `StartGameUseCase.start_game(mode, priority, other) -> Game`, `RevealCellUseCase.reveal(game_id, player_id, x, y) -> None`, `ForfeitUseCase.forfeit(game_id, player_id) -> None`, `GetGameUseCase.get_game(game_id, player_id) -> Game`; 프로토콜 `GameStore`(save·get·find_active_by_player), `GameEventPublisher`(game_started·publish), `TurnTimer.schedule(game_id, turn_seq, deadline_ms, on_expire)`; `GameService(store, publisher, timer, layout_generator, clock, first_seat_chooser=..., id_factory=...)` — 위 네 유스케이스와 `handle_timeout(game_id, turn_seq)`; `InMemoryGameStore()`.

- [ ] **Step 1: 실패하는 테스트 작성**

`server/tests/game/test_game_service.py`:

```python
import threading

import pytest

from fakes import FakeClock, FakeGameEventPublisher, FakeTurnTimer
from wheresmeow.game.adapter.outbound.memory.in_memory_game_store import InMemoryGameStore
from wheresmeow.game.application.port.inbound import GamePlayer
from wheresmeow.game.application.service.game_service import GameService
from wheresmeow.game.domain.board import FixedMineLayoutGenerator
from wheresmeow.game.domain.errors import AlreadyInGame, GameNotFound, NotAParticipant
from wheresmeow.game.domain.game import TURN_MS, CellsRevealed, GameEnded, GameMode, TurnTimedOut
from wheresmeow.game.domain.skins import SkinPreference

# 12x12 판. 고양이를 아래쪽 두 줄과 (11,9) 에 몰아 두어 (0,0) 은 빈 칸이다.
CATS = {(x, y) for y in range(10, 12) for x in range(0, 12)} | {(11, 9)}  # 24 + 1 = 25
HOST = GamePlayer("host", "방장", SkinPreference(16, 17))
GUEST = GamePlayer("guest", "손님", SkinPreference(16, 20))


@pytest.fixture
def env():
    clock = FakeClock(now_ms=0)
    store = InMemoryGameStore()
    publisher = FakeGameEventPublisher()
    timer = FakeTurnTimer()
    service = GameService(
        store,
        publisher,
        timer,
        FixedMineLayoutGenerator(CATS),
        clock,
        first_seat_chooser=lambda: 0,
        id_factory=lambda: "g1",
    )
    return service, store, publisher, timer, clock


class TestGameService:
    class TestStartGame:
        def test_성공_대국을_만들고_시작을_알리고_첫_턴_타이머를_예약한다(self, env):
            service, store, publisher, timer, _ = env

            game = service.start_game(GameMode.INVITE, HOST, GUEST)

            assert store.get("g1") is game
            assert publisher.started == [game]
            assert [(gid, seq, deadline) for gid, seq, deadline, _ in timer.scheduled] == [("g1", 1, TURN_MS)]

        def test_성공_우선권자가_좌석_0이고_1P가_겹치면_상대가_2P를_쓴다(self, env):
            service, *_ = env

            game = service.start_game(GameMode.INVITE, HOST, GUEST)

            assert game.seats[0].player_id == "host"
            assert (game.seats[0].skin, game.seats[1].skin) == (16, 20)

        def test_실패_진행_중인_대국이_있으면_거부한다(self, env):
            service, *_ = env
            service.start_game(GameMode.INVITE, HOST, GUEST)

            with pytest.raises(AlreadyInGame):
                service.start_game(GameMode.INVITE, HOST, GamePlayer("other", "다른", SkinPreference()))

    class TestReveal:
        def test_성공_이벤트를_발행하고_다음_턴_타이머를_예약한다(self, env):
            service, _, publisher, timer, clock = env
            service.start_game(GameMode.INVITE, HOST, GUEST)
            clock.advance(3000)

            service.reveal("g1", "host", 0, 0)

            [(game_id, [event])] = publisher.published
            assert game_id == "g1"
            assert isinstance(event, CellsRevealed)
            assert timer.scheduled[-1][:3] == ("g1", 2, 3000 + TURN_MS)

        def test_성공_대국이_끝나면_타이머를_예약하지_않고_새_대국을_시작할_수_있다(self, env):
            service, _, publisher, timer, _ = env
            service.start_game(GameMode.INVITE, HOST, GUEST)
            scheduled_before = len(timer.scheduled)

            service.forfeit("g1", "guest")

            assert isinstance(publisher.published[-1][1][-1], GameEnded)
            assert len(timer.scheduled) == scheduled_before
            service.start_game(GameMode.INVITE, HOST, GUEST)  # 예외 없음

        def test_실패_없는_대국이면_거부한다(self, env):
            service, *_ = env

            with pytest.raises(GameNotFound):
                service.reveal("nope", "host", 0, 0)

        def test_성공_같은_칸을_동시에_두_번_눌러도_한_번만_적용된다(self, env):
            service, _, publisher, _, _ = env
            service.start_game(GameMode.INVITE, HOST, GUEST)
            errors: list[Exception] = []

            def tap():
                try:
                    service.reveal("g1", "host", 11, 9)  # 고양이 칸
                except Exception as error:  # noqa: BLE001 - 두 번째 요청의 예외를 모은다
                    errors.append(error)

            threads = [threading.Thread(target=tap) for _ in range(2)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

            assert len(publisher.published) == 1
            assert [type(e).__name__ for e in errors] == ["CellAlreadyOpen"]

    class TestHandleTimeout:
        def test_성공_만료되면_감점_이벤트를_발행한다(self, env):
            service, _, publisher, timer, _ = env
            service.start_game(GameMode.INVITE, HOST, GUEST)

            timer.fire_latest()

            [(_, [event])] = publisher.published
            assert isinstance(event, TurnTimedOut)
            assert event.scores == (-1, 0)

        def test_성공_지나간_턴의_만료는_아무것도_발행하지_않는다(self, env):
            service, _, publisher, timer, _ = env
            service.start_game(GameMode.INVITE, HOST, GUEST)
            first_turn = timer.scheduled[0]
            service.reveal("g1", "host", 0, 0)
            published_before = len(publisher.published)

            first_turn[3]("g1", first_turn[1])

            assert len(publisher.published) == published_before

        def test_성공_기권으로_끝난_뒤_이전_턴의_만료는_아무것도_발행하지_않는다(self, env):
            service, _, publisher, timer, _ = env
            service.start_game(GameMode.INVITE, HOST, GUEST)
            service.forfeit("g1", "guest")
            published_before = len(publisher.published)

            timer.fire_latest()  # 시작 시 예약된 첫 턴 타이머

            assert len(publisher.published) == published_before

        def test_성공_없는_대국의_만료는_무시한다(self, env):
            service, *_ = env

            service.handle_timeout("nope", 1)  # 예외 없음

    class TestGetGame:
        def test_성공_참가자는_대국을_조회한다(self, env):
            service, *_ = env
            service.start_game(GameMode.INVITE, HOST, GUEST)

            assert service.get_game("g1", "guest").id == "g1"

        def test_실패_참가자가_아니면_거부한다(self, env):
            service, *_ = env
            service.start_game(GameMode.INVITE, HOST, GUEST)

            with pytest.raises(NotAParticipant):
                service.get_game("g1", "stranger")
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `cd server && .venv/bin/pytest tests/game/test_game_service.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'wheresmeow.game.adapter'`

- [ ] **Step 3: 포트 작성**

`server/src/wheresmeow/game/application/port/inbound.py`:

```python
"""game 도메인이 바깥(어댑터, 다른 도메인)에 제공하는 유스케이스."""

from dataclasses import dataclass
from typing import Protocol

from wheresmeow.game.domain.game import Game, GameMode
from wheresmeow.game.domain.skins import SkinPreference


@dataclass(frozen=True)
class GamePlayer:
    player_id: str
    nickname: str
    skins: SkinPreference


class StartGameUseCase(Protocol):
    def start_game(self, mode: GameMode, priority: GamePlayer, other: GamePlayer) -> Game:
        """priority 가 스킨 우선권자이며 좌석 0 에 앉는다."""
        ...


class RevealCellUseCase(Protocol):
    def reveal(self, game_id: str, player_id: str, x: int, y: int) -> None: ...


class ForfeitUseCase(Protocol):
    def forfeit(self, game_id: str, player_id: str) -> None: ...


class GetGameUseCase(Protocol):
    def get_game(self, game_id: str, player_id: str) -> Game: ...
```

`server/src/wheresmeow/game/application/port/outbound.py`:

```python
"""game 도메인이 바깥에 요구하는 기능."""

from collections.abc import Callable, Sequence
from typing import Protocol

from wheresmeow.game.domain.game import Game, GameEvent


class GameStore(Protocol):
    def save(self, game: Game) -> None: ...

    def get(self, game_id: str) -> Game | None: ...

    def find_active_by_player(self, player_id: str) -> Game | None: ...


class GameEventPublisher(Protocol):
    def game_started(self, game: Game) -> None: ...

    def publish(self, game: Game, events: Sequence[GameEvent]) -> None: ...


class TurnTimer(Protocol):
    def schedule(
        self,
        game_id: str,
        turn_seq: int,
        deadline_ms: int,
        on_expire: Callable[[str, int], None],
    ) -> None:
        """deadline_ms 가 지나면 on_expire(game_id, turn_seq) 를 호출한다."""
        ...
```

- [ ] **Step 4: 서비스와 메모리 저장소 구현**

이벤트 발행과 다음 턴 타이머 예약을 대국 잠금 **안에서** 한다. 잠금 밖에서 발행하면 두 동작의 이벤트가 `version` 순서와 다르게 나갈 수 있다.

`server/src/wheresmeow/game/application/service/game_service.py`:

```python
import secrets
import threading
import uuid
from collections.abc import Callable, Sequence

from wheresmeow.game.application.port.inbound import GamePlayer
from wheresmeow.game.application.port.outbound import GameEventPublisher, GameStore, TurnTimer
from wheresmeow.game.domain.board import BOARD_SIZE, CAT_COUNT, Board, MineLayoutGenerator
from wheresmeow.game.domain.errors import AlreadyInGame, GameNotFound
from wheresmeow.game.domain.game import Game, GameEvent, GameMode, GameStatus, Seat
from wheresmeow.game.domain.skins import assign_skins
from wheresmeow.shared.clock import Clock


class GameService:
    """StartGame·RevealCell·Forfeit·GetGame 유스케이스 구현.

    대국마다 잠금 하나를 두어 reveal·timeout·forfeit 가 순서대로 적용되게 한다.
    운영(gevent)에서는 monkey patch 로 threading.Lock 이 gevent 잠금이 된다.
    이벤트 발행과 타이머 예약도 잠금 안에서 해서 version 순서가 뒤바뀌지 않게 한다.
    """

    def __init__(
        self,
        store: GameStore,
        publisher: GameEventPublisher,
        timer: TurnTimer,
        layout_generator: MineLayoutGenerator,
        clock: Clock,
        first_seat_chooser: Callable[[], int] = lambda: secrets.randbelow(2),
        id_factory: Callable[[], str] = lambda: uuid.uuid4().hex,
    ) -> None:
        self._store = store
        self._publisher = publisher
        self._timer = timer
        self._layout_generator = layout_generator
        self._clock = clock
        self._first_seat_chooser = first_seat_chooser
        self._id_factory = id_factory
        self._locks: dict[str, threading.Lock] = {}
        self._locks_guard = threading.Lock()

    def start_game(self, mode: GameMode, priority: GamePlayer, other: GamePlayer) -> Game:
        for player in (priority, other):
            if self._store.find_active_by_player(player.player_id) is not None:
                raise AlreadyInGame(f"이미 진행 중인 대국이 있습니다: {player.player_id}")
        skin_0, skin_1 = assign_skins(priority.skins, other.skins)
        board = Board(BOARD_SIZE, self._layout_generator.generate(BOARD_SIZE, CAT_COUNT))
        seats = (
            Seat(priority.player_id, priority.nickname, skin_0),
            Seat(other.player_id, other.nickname, skin_1),
        )
        game = Game(self._id_factory(), mode, board, seats, self._first_seat_chooser(), self._clock.now_ms())
        with self._lock_for(game.id):
            self._store.save(game)
            self._publisher.game_started(game)
            self._schedule_turn(game)
        return game

    def reveal(self, game_id: str, player_id: str, x: int, y: int) -> None:
        self._act(game_id, lambda game: game.reveal(player_id, x, y, self._clock.now_ms()))

    def forfeit(self, game_id: str, player_id: str) -> None:
        self._act(game_id, lambda game: game.forfeit(player_id, self._clock.now_ms()))

    def handle_timeout(self, game_id: str, turn_seq: int) -> None:
        """TurnTimer 콜백. 그 사이 대국이 사라졌으면 아무것도 하지 않는다."""
        if self._store.get(game_id) is None:
            return
        self._act(game_id, lambda game: game.timeout(turn_seq, self._clock.now_ms()))

    def get_game(self, game_id: str, player_id: str) -> Game:
        game = self._require(game_id)
        game.seat_of(player_id)  # 참가자가 아니면 NotAParticipant
        return game

    def _act(self, game_id: str, action: Callable[[Game], Sequence[GameEvent]]) -> None:
        game = self._require(game_id)
        with self._lock_for(game_id):
            events = action(game)
            if not events:
                return
            self._store.save(game)
            self._publisher.publish(game, events)
            if game.status is GameStatus.IN_PROGRESS:
                self._schedule_turn(game)
        if game.status is GameStatus.FINISHED:
            with self._locks_guard:
                self._locks.pop(game_id, None)

    def _schedule_turn(self, game: Game) -> None:
        assert game.turn_deadline_ms is not None
        self._timer.schedule(game.id, game.turn_seq, game.turn_deadline_ms, self.handle_timeout)

    def _require(self, game_id: str) -> Game:
        game = self._store.get(game_id)
        if game is None:
            raise GameNotFound(f"대국을 찾을 수 없습니다: {game_id}")
        return game

    def _lock_for(self, game_id: str) -> threading.Lock:
        with self._locks_guard:
            return self._locks.setdefault(game_id, threading.Lock())
```

`server/src/wheresmeow/game/adapter/outbound/memory/in_memory_game_store.py`:

```python
import threading

from wheresmeow.game.domain.game import Game, GameStatus


class InMemoryGameStore:
    """단일 프로세스용. 끝난 대국도 결과 화면을 위해 남겨 둔다."""

    def __init__(self) -> None:
        self._games: dict[str, Game] = {}
        self._guard = threading.Lock()

    def save(self, game: Game) -> None:
        with self._guard:
            self._games[game.id] = game

    def get(self, game_id: str) -> Game | None:
        with self._guard:
            return self._games.get(game_id)

    def find_active_by_player(self, player_id: str) -> Game | None:
        with self._guard:
            return next(
                (
                    g
                    for g in self._games.values()
                    if g.status is GameStatus.IN_PROGRESS and g.is_participant(player_id)
                ),
                None,
            )
```

- [ ] **Step 5: 테스트 통과 확인**

Run: `cd server && .venv/bin/pytest tests/game/test_game_service.py -v`
Expected: PASS (13 passed)

동시성 테스트가 우연히 통과한 것이 아닌지 반복 실행으로 확인한다.

Run: `cd server && for i in $(seq 1 30); do .venv/bin/pytest -q -k 동시에 | tail -1; done | sort | uniq -c`
Expected: 30줄 모두 통과(`30 .` 한 줄)

- [ ] **Step 6: 커밋**

```bash
git add server/src/wheresmeow/game server/tests/game/test_game_service.py
git commit -m "feat: 대국 유스케이스와 메모리 저장소 구현"
```

---

### Task 6: 게스트 플레이어(account 도메인)

**Files:**
- Create: `server/src/wheresmeow/account/domain/player.py`
- Create: `server/src/wheresmeow/account/application/port/inbound.py`
- Create: `server/src/wheresmeow/account/application/port/outbound.py`
- Create: `server/src/wheresmeow/account/application/service/guest_service.py`
- Create: `server/src/wheresmeow/account/adapter/outbound/memory/in_memory_player_store.py`
- Create: `server/src/wheresmeow/account/adapter/outbound/token/signed_token_issuer.py`
- Test: `server/tests/account/test_guest.py`

**Interfaces:**
- Consumes: `DomainError`, `InvalidInput`, `Unauthorized` (Task 1)
- Produces: `PlayerKind`(MEMBER·GUEST), `Player(id, kind, nickname, skin_1p=16, skin_2p=17)`, `normalize_nickname(raw) -> str`; `GuestCredentials(player, token)`; 프로토콜 `CreateGuestUseCase.create_guest(nickname)`, `AuthenticateUseCase.authenticate(token) -> Player`, `GetPlayerUseCase.get_player(player_id) -> Player`, `PlayerStore`(save·get), `TokenIssuer`(issue·verify); `GuestService(store, tokens, id_factory=...)`(위 세 유스케이스 구현), `PlayerNotFound`(code `PLAYER_NOT_FOUND`); `InMemoryPlayerStore()`; `SignedTokenIssuer(secret_key, max_age_seconds=30일)`.

- [ ] **Step 1: 실패하는 테스트 작성**

`server/tests/account/test_guest.py`:

```python
import pytest

from wheresmeow.account.adapter.outbound.memory.in_memory_player_store import InMemoryPlayerStore
from wheresmeow.account.adapter.outbound.token.signed_token_issuer import SignedTokenIssuer
from wheresmeow.account.application.service.guest_service import GuestService, PlayerNotFound
from wheresmeow.account.domain.player import PlayerKind, normalize_nickname
from wheresmeow.shared.errors import InvalidInput, Unauthorized


class TestNormalizeNickname:
    class TestNormalize:
        def test_성공_앞뒤_공백을_제거한다(self):
            assert normalize_nickname("  냥냥  ") == "냥냥"

        @pytest.mark.parametrize("raw", ["냥", "   냥  ", "가" * 13, ""])
        def test_실패_2자_미만이거나_12자_초과면_거부한다(self, raw):
            with pytest.raises(InvalidInput):
                normalize_nickname(raw)


class TestSignedTokenIssuer:
    class TestVerify:
        def test_성공_발급한_토큰에서_player_id를_꺼낸다(self):
            issuer = SignedTokenIssuer("secret")

            assert issuer.verify(issuer.issue("p1")) == "p1"

        def test_실패_다른_키로_서명한_토큰이면_거부한다(self):
            token = SignedTokenIssuer("other").issue("p1")

            with pytest.raises(Unauthorized):
                SignedTokenIssuer("secret").verify(token)

        def test_실패_만료된_토큰이면_거부한다(self):
            issuer = SignedTokenIssuer("secret", max_age_seconds=-1)

            with pytest.raises(Unauthorized):
                issuer.verify(issuer.issue("p1"))

    class TestInit:
        def test_실패_서명_키가_비어_있으면_거부한다(self):
            with pytest.raises(ValueError):
                SignedTokenIssuer("")


class TestGuestService:
    @pytest.fixture
    def service(self):
        return GuestService(InMemoryPlayerStore(), SignedTokenIssuer("secret"), id_factory=lambda: "p1")

    class TestCreateGuest:
        def test_성공_게스트를_만들고_기본_스킨과_토큰을_준다(self, service):
            credentials = service.create_guest(" 고양이집사 ")

            player = credentials.player
            assert (player.id, player.kind, player.nickname) == ("p1", PlayerKind.GUEST, "고양이집사")
            assert (player.skin_1p, player.skin_2p) == (16, 17)
            assert service.authenticate(credentials.token) is player

        def test_실패_닉네임이_규칙에_맞지_않으면_거부한다(self, service):
            with pytest.raises(InvalidInput):
                service.create_guest("냥")

    class TestAuthenticate:
        def test_실패_저장소에_없는_플레이어의_토큰이면_거부한다(self, service):
            token = SignedTokenIssuer("secret").issue("ghost")

            with pytest.raises(Unauthorized):
                service.authenticate(token)

    class TestGetPlayer:
        def test_실패_없는_플레이어면_거부한다(self, service):
            with pytest.raises(PlayerNotFound):
                service.get_player("ghost")
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `cd server && .venv/bin/pytest tests/account -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'wheresmeow.account'`

- [ ] **Step 3: 도메인과 포트 작성**

`server/src/wheresmeow/account/domain/player.py`:

```python
from dataclasses import dataclass
from enum import StrEnum

from wheresmeow.shared.errors import InvalidInput

NICKNAME_MIN_LENGTH = 2
NICKNAME_MAX_LENGTH = 12
DEFAULT_SKIN_1P = 16
DEFAULT_SKIN_2P = 17


class PlayerKind(StrEnum):
    MEMBER = "MEMBER"
    GUEST = "GUEST"


def normalize_nickname(raw: str) -> str:
    nickname = raw.strip()
    if not NICKNAME_MIN_LENGTH <= len(nickname) <= NICKNAME_MAX_LENGTH:
        raise InvalidInput(
            f"닉네임은 {NICKNAME_MIN_LENGTH}~{NICKNAME_MAX_LENGTH}자여야 합니다: {nickname!r}"
        )
    return nickname


@dataclass
class Player:
    id: str
    kind: PlayerKind
    nickname: str
    skin_1p: int = DEFAULT_SKIN_1P
    skin_2p: int = DEFAULT_SKIN_2P
```

`server/src/wheresmeow/account/application/port/inbound.py`:

```python
from dataclasses import dataclass
from typing import Protocol

from wheresmeow.account.domain.player import Player


@dataclass(frozen=True)
class GuestCredentials:
    player: Player
    token: str


class CreateGuestUseCase(Protocol):
    def create_guest(self, nickname: str) -> GuestCredentials: ...


class AuthenticateUseCase(Protocol):
    def authenticate(self, token: str) -> Player:
        """토큰이 유효하지 않거나 플레이어가 없으면 Unauthorized."""
        ...


class GetPlayerUseCase(Protocol):
    def get_player(self, player_id: str) -> Player: ...
```

`server/src/wheresmeow/account/application/port/outbound.py`:

```python
from typing import Protocol

from wheresmeow.account.domain.player import Player


class PlayerStore(Protocol):
    def save(self, player: Player) -> None: ...

    def get(self, player_id: str) -> Player | None: ...


class TokenIssuer(Protocol):
    def issue(self, player_id: str) -> str: ...

    def verify(self, token: str) -> str:
        """player_id 를 돌려준다. 위조·만료면 Unauthorized."""
        ...
```

- [ ] **Step 4: 서비스와 어댑터 구현**

`server/src/wheresmeow/account/application/service/guest_service.py`:

```python
import uuid
from collections.abc import Callable

from wheresmeow.account.application.port.inbound import GuestCredentials
from wheresmeow.account.application.port.outbound import PlayerStore, TokenIssuer
from wheresmeow.account.domain.player import Player, PlayerKind, normalize_nickname
from wheresmeow.shared.errors import DomainError, Unauthorized


class PlayerNotFound(DomainError):
    code = "PLAYER_NOT_FOUND"


class GuestService:
    """CreateGuest·Authenticate·GetPlayer 유스케이스 구현."""

    def __init__(
        self,
        store: PlayerStore,
        tokens: TokenIssuer,
        id_factory: Callable[[], str] = lambda: uuid.uuid4().hex,
    ) -> None:
        self._store = store
        self._tokens = tokens
        self._id_factory = id_factory

    def create_guest(self, nickname: str) -> GuestCredentials:
        player = Player(self._id_factory(), PlayerKind.GUEST, normalize_nickname(nickname))
        self._store.save(player)
        return GuestCredentials(player, self._tokens.issue(player.id))

    def authenticate(self, token: str) -> Player:
        player = self._store.get(self._tokens.verify(token))
        if player is None:
            raise Unauthorized("플레이어가 존재하지 않습니다")
        return player

    def get_player(self, player_id: str) -> Player:
        player = self._store.get(player_id)
        if player is None:
            raise PlayerNotFound(f"플레이어를 찾을 수 없습니다: {player_id}")
        return player
```

`server/src/wheresmeow/account/adapter/outbound/memory/in_memory_player_store.py`:

```python
import threading

from wheresmeow.account.domain.player import Player


class InMemoryPlayerStore:
    def __init__(self) -> None:
        self._players: dict[str, Player] = {}
        self._guard = threading.Lock()

    def save(self, player: Player) -> None:
        with self._guard:
            self._players[player.id] = player

    def get(self, player_id: str) -> Player | None:
        with self._guard:
            return self._players.get(player_id)
```

`server/src/wheresmeow/account/adapter/outbound/token/signed_token_issuer.py`:

```python
from itsdangerous import BadSignature, URLSafeTimedSerializer

from wheresmeow.shared.errors import Unauthorized

GUEST_TOKEN_MAX_AGE_SECONDS = 30 * 24 * 60 * 60


class SignedTokenIssuer:
    """게스트 토큰. 서버 비밀 키로 서명한 player_id 이며 30일 뒤 만료된다."""

    def __init__(self, secret_key: str, max_age_seconds: int = GUEST_TOKEN_MAX_AGE_SECONDS) -> None:
        if not secret_key:
            raise ValueError("서명 키가 비어 있습니다")
        self._serializer = URLSafeTimedSerializer(secret_key, salt="wheresmeow-guest")
        self._max_age = max_age_seconds

    def issue(self, player_id: str) -> str:
        return self._serializer.dumps(player_id)

    def verify(self, token: str) -> str:
        try:
            # SignatureExpired 는 BadSignature 의 하위 클래스다
            return self._serializer.loads(token, max_age=self._max_age)
        except BadSignature as error:
            raise Unauthorized("유효하지 않은 토큰입니다") from error
```

- [ ] **Step 5: 테스트 통과 확인**

Run: `cd server && .venv/bin/pytest tests/account -v`
Expected: PASS (13 passed)

- [ ] **Step 6: 커밋**

```bash
git add server/src/wheresmeow/account server/tests/account
git commit -m "feat: 게스트 플레이어 생성과 서명 토큰 인증 구현"
```

---

### Task 7: 초대 방(room 도메인)

**Files:**
- Create: `server/src/wheresmeow/room/domain/room.py`
- Create: `server/src/wheresmeow/room/application/port/inbound.py`
- Create: `server/src/wheresmeow/room/application/port/outbound.py`
- Create: `server/src/wheresmeow/room/application/service/room_service.py`
- Create: `server/src/wheresmeow/room/adapter/outbound/memory/in_memory_room_store.py`
- Test: `server/tests/room/test_room.py`

**Interfaces:**
- Consumes: `DomainError`, `Clock` (Task 1); 테스트에서 `AlreadyInGame` (Task 3), `FakeClock` (Task 1)
- Produces: `ROOM_CODE_ALPHABET`, `ROOM_CODE_LENGTH = 6`, `ROOM_TTL_MS`; 예외 `RoomNotFound`, `RoomFull`, `RoomExpired`, `NotRoomHost`; `generate_room_code(rng)`; `RoomStatus`(WAITING·STARTED·CANCELLED); `Room(code, host_id, created_at_ms)` — `expires_at_ms`, `ensure_open(now)`, `admit(player_id, now) -> JoinResult`, `start(guest_id, game_id)`, `cancel(player_id)`; `RoomJoinOutcome(room, game_id | None)`; 프로토콜 `CreateRoomUseCase`, `GetRoomUseCase`, `JoinRoomUseCase`, `CancelRoomUseCase`, `RoomStore`, `PlayerDirectory.profile(player_id) -> PlayerProfile`, `GameStarter.start_invite_game(host, guest) -> str`; `PlayerProfile(player_id, nickname, skin_1p, skin_2p)`; `RoomService(store, players, game_starter, clock, code_factory=...)`; `InMemoryRoomStore()`.

- [ ] **Step 1: 실패하는 테스트 작성**

`server/tests/room/test_room.py`:

```python
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
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `cd server && .venv/bin/pytest tests/room/test_room.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'wheresmeow.room'`

- [ ] **Step 3: 도메인과 포트 작성**

`server/src/wheresmeow/room/domain/room.py`:

```python
"""초대 방. 방장과 상대 한 명이 모이면 대국을 시작한다."""

import random
from dataclasses import dataclass
from enum import StrEnum

from wheresmeow.shared.errors import DomainError

ROOM_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # 0·O·1·I 제외
ROOM_CODE_LENGTH = 6
ROOM_TTL_MS = 10 * 60 * 1000


class RoomNotFound(DomainError):
    code = "ROOM_NOT_FOUND"


class RoomFull(DomainError):
    code = "ROOM_FULL"


class RoomExpired(DomainError):
    code = "ROOM_EXPIRED"


class NotRoomHost(DomainError):
    code = "NOT_ROOM_HOST"


def generate_room_code(rng: random.Random) -> str:
    return "".join(rng.choice(ROOM_CODE_ALPHABET) for _ in range(ROOM_CODE_LENGTH))


class RoomStatus(StrEnum):
    WAITING = "WAITING"
    STARTED = "STARTED"
    CANCELLED = "CANCELLED"


class JoinResult(StrEnum):
    HOST_WAITING = "HOST_WAITING"  # 방장이 들어와 상대를 기다린다
    OPPONENT_ARRIVED = "OPPONENT_ARRIVED"  # 상대가 왔으니 대국을 시작해야 한다


@dataclass
class Room:
    code: str
    host_id: str
    created_at_ms: int
    status: RoomStatus = RoomStatus.WAITING
    guest_id: str | None = None
    game_id: str | None = None

    @property
    def expires_at_ms(self) -> int:
        return self.created_at_ms + ROOM_TTL_MS

    def ensure_open(self, now_ms: int) -> None:
        if self.status is RoomStatus.CANCELLED or (
            self.status is RoomStatus.WAITING and now_ms >= self.expires_at_ms
        ):
            raise RoomExpired(f"만료되었거나 취소된 방입니다: {self.code}")

    def admit(self, player_id: str, now_ms: int) -> JoinResult:
        """입장 판정만 한다. 대국 시작에 성공한 뒤 start() 로 상태를 바꾼다."""
        self.ensure_open(now_ms)
        if self.status is RoomStatus.STARTED:
            raise RoomFull(f"이미 대국이 시작된 방입니다: {self.code}")
        if player_id == self.host_id:
            return JoinResult.HOST_WAITING
        return JoinResult.OPPONENT_ARRIVED

    def start(self, guest_id: str, game_id: str) -> None:
        if self.status is not RoomStatus.WAITING:
            raise RoomFull(f"이미 대국이 시작된 방입니다: {self.code}")
        self.status = RoomStatus.STARTED
        self.guest_id = guest_id
        self.game_id = game_id

    def cancel(self, player_id: str) -> None:
        if player_id != self.host_id:
            raise NotRoomHost("방장만 방을 취소할 수 있습니다")
        if self.status is RoomStatus.WAITING:
            self.status = RoomStatus.CANCELLED
```

`server/src/wheresmeow/room/application/port/inbound.py`:

```python
from dataclasses import dataclass
from typing import Protocol

from wheresmeow.room.domain.room import Room


@dataclass(frozen=True)
class RoomJoinOutcome:
    room: Room
    game_id: str | None  # None 이면 방장이 대기 중


class CreateRoomUseCase(Protocol):
    def create_room(self, host_id: str) -> Room: ...


class GetRoomUseCase(Protocol):
    def get_room(self, code: str) -> Room: ...


class JoinRoomUseCase(Protocol):
    def join(self, code: str, player_id: str) -> RoomJoinOutcome: ...


class CancelRoomUseCase(Protocol):
    def cancel(self, code: str, player_id: str) -> None: ...
```

`server/src/wheresmeow/room/application/port/outbound.py`:

```python
from dataclasses import dataclass
from typing import Protocol

from wheresmeow.room.domain.room import Room


@dataclass(frozen=True)
class PlayerProfile:
    player_id: str
    nickname: str
    skin_1p: int
    skin_2p: int


class RoomStore(Protocol):
    def save(self, room: Room) -> None: ...

    def get(self, code: str) -> Room | None: ...


class PlayerDirectory(Protocol):
    def profile(self, player_id: str) -> PlayerProfile: ...


class GameStarter(Protocol):
    def start_invite_game(self, host: PlayerProfile, guest: PlayerProfile) -> str:
        """대국을 시작하고 game_id 를 돌려준다. 방장이 스킨 우선권을 갖는다."""
        ...
```

- [ ] **Step 4: 서비스와 메모리 저장소 구현**

`join`은 입장 판정(`admit`)만 먼저 하고, 대국 시작에 성공한 뒤에야 `room.start()`로 상태를 바꾼다. 그래서 대국 시작이 실패해도(예: 손님이 이미 다른 대국 중) 방은 대기 상태로 남는다.

`server/src/wheresmeow/room/application/service/room_service.py`:

```python
import random
import threading
from collections.abc import Callable

from wheresmeow.room.application.port.inbound import RoomJoinOutcome
from wheresmeow.room.application.port.outbound import GameStarter, PlayerDirectory, RoomStore
from wheresmeow.room.domain.room import JoinResult, Room, RoomNotFound, generate_room_code
from wheresmeow.shared.clock import Clock

MAX_CODE_ATTEMPTS = 20


class RoomService:
    """CreateRoom·GetRoom·JoinRoom·CancelRoom 유스케이스 구현."""

    def __init__(
        self,
        store: RoomStore,
        players: PlayerDirectory,
        game_starter: GameStarter,
        clock: Clock,
        code_factory: Callable[[], str] = lambda: generate_room_code(random.SystemRandom()),
    ) -> None:
        self._store = store
        self._players = players
        self._game_starter = game_starter
        self._clock = clock
        self._code_factory = code_factory
        self._guard = threading.Lock()  # 같은 방에 두 사람이 동시에 들어오는 경쟁을 막는다

    def create_room(self, host_id: str) -> Room:
        self._players.profile(host_id)  # 없는 플레이어면 여기서 실패한다
        with self._guard:
            for _ in range(MAX_CODE_ATTEMPTS):
                code = self._code_factory()
                if self._store.get(code) is None:
                    room = Room(code, host_id, self._clock.now_ms())
                    self._store.save(room)
                    return room
        raise RuntimeError("사용하지 않는 방 코드를 찾지 못했습니다")

    def get_room(self, code: str) -> Room:
        room = self._require(code)
        room.ensure_open(self._clock.now_ms())
        return room

    def join(self, code: str, player_id: str) -> RoomJoinOutcome:
        with self._guard:
            room = self._require(code)
            if room.admit(player_id, self._clock.now_ms()) is JoinResult.HOST_WAITING:
                return RoomJoinOutcome(room, None)
            host = self._players.profile(room.host_id)
            guest = self._players.profile(player_id)
            game_id = self._game_starter.start_invite_game(host, guest)
            room.start(player_id, game_id)
            self._store.save(room)
            return RoomJoinOutcome(room, game_id)

    def cancel(self, code: str, player_id: str) -> None:
        with self._guard:
            room = self._require(code)
            room.cancel(player_id)
            self._store.save(room)

    def _require(self, code: str) -> Room:
        room = self._store.get(code.upper())
        if room is None:
            raise RoomNotFound(f"방을 찾을 수 없습니다: {code}")
        return room
```

`server/src/wheresmeow/room/adapter/outbound/memory/in_memory_room_store.py`:

```python
import threading

from wheresmeow.room.domain.room import Room


class InMemoryRoomStore:
    """만료된 방도 남아 있다. 1단계에서는 메모리 정리를 하지 않는다(재시작 시 비워짐)."""

    def __init__(self) -> None:
        self._rooms: dict[str, Room] = {}
        self._guard = threading.Lock()

    def save(self, room: Room) -> None:
        with self._guard:
            self._rooms[room.code] = room

    def get(self, code: str) -> Room | None:
        with self._guard:
            return self._rooms.get(code)
```

- [ ] **Step 5: 테스트 통과 확인**

Run: `cd server && .venv/bin/pytest tests/room/test_room.py -v`
Expected: PASS (12 passed)

- [ ] **Step 6: 커밋**

```bash
git add server/src/wheresmeow/room server/tests/room
git commit -m "feat: 초대 방 생성·입장·만료·취소 구현"
```

---

### Task 8: 대국 outbound 어댑터(페이로드, 이벤트 발행, 턴 타이머)

**Files:**
- Create: `server/src/wheresmeow/shared/socket_rooms.py`
- Create: `server/src/wheresmeow/game/adapter/outbound/socket/payloads.py`
- Create: `server/src/wheresmeow/game/adapter/outbound/socket/socketio_game_event_publisher.py`
- Create: `server/src/wheresmeow/game/adapter/outbound/timer/background_turn_timer.py`
- Test: `server/tests/game/test_payloads.py`
- Test: `server/tests/game/test_background_turn_timer.py`

**Interfaces:**
- Consumes: `Game`, `OpenedCell`, 이벤트들 (Task 4); `Clock`, `SystemClock` (Task 1)
- Produces: `player_room(player_id) -> "player:{id}"`; `cell_payload(cell)`, `started_payload(game, my_seat)`, `event_payload(game_id, event) -> (이벤트 이름, dict)`; `SocketIOGameEventPublisher(socketio)`(GameEventPublisher 구현); `BackgroundTurnTimer(socketio, clock)`(TurnTimer 구현). 페이로드 필드 이름은 웹 `src/game/types.ts`(Task 10)와 정확히 같아야 한다.

- [ ] **Step 1: 실패하는 테스트 작성**

`server/tests/game/test_payloads.py`:

```python
from wheresmeow.game.adapter.outbound.socket.payloads import cell_payload, event_payload, started_payload
from wheresmeow.game.domain.board import Board
from wheresmeow.game.domain.game import Game, GameMode, OpenedCell, Seat


def make_game() -> Game:
    seats = (Seat("a", "에이", 16), Seat("b", "비", 17))
    return Game("g1", GameMode.INVITE, Board(4, frozenset({(0, 0), (3, 3)})), seats, 0, 0)


class TestPayloads:
    class TestCellPayload:
        def test_성공_숫자_칸은_n을_담는다(self):
            assert cell_payload(OpenedCell(1, 2, 3, None)) == {"x": 1, "y": 2, "kind": "number", "n": 3}

        def test_성공_고양이_칸은_찾은_좌석을_담는다(self):
            assert cell_payload(OpenedCell(0, 0, None, 1)) == {"x": 0, "y": 0, "kind": "cat", "seat": 1}

    class TestStartedPayload:
        def test_성공_진행_중_페이로드에는_고양이_위치가_없다(self):
            payload = started_payload(make_game(), my_seat=1)

            assert payload["mySeat"] == 1
            assert "cats" not in payload
            assert "(3, 3)" not in str(payload) and "[3, 3]" not in str(payload)

    class TestEventPayload:
        def test_성공_종료_이벤트에만_고양이_위치를_담는다(self):
            game = make_game()
            [ended] = game.forfeit("a", now_ms=0)

            name, payload = event_payload(game.id, ended)

            assert name == "game:ended"
            assert payload["cats"] == [[0, 0], [3, 3]]
            assert (payload["reason"], payload["winner"]) == ("FORFEIT", 1)

        def test_성공_공개_이벤트의_이름과_필드(self):
            game = make_game()
            [revealed] = game.reveal("a", 1, 0, now_ms=0)

            name, payload = event_payload(game.id, revealed)

            assert name == "game:revealed"
            assert payload["cells"] == [{"x": 1, "y": 0, "kind": "number", "n": 1}]
            assert payload["currentSeat"] == 1
```

`server/tests/game/test_background_turn_timer.py`:

```python
import logging
import threading

from flask import Flask
from flask_socketio import SocketIO

from wheresmeow.game.adapter.outbound.timer.background_turn_timer import BackgroundTurnTimer
from wheresmeow.shared.clock import SystemClock


def make_timer() -> tuple[BackgroundTurnTimer, SystemClock]:
    clock = SystemClock()
    return BackgroundTurnTimer(SocketIO(Flask(__name__), async_mode="threading"), clock), clock


class TestBackgroundTurnTimer:
    class TestSchedule:
        def test_성공_마감_시각이_지나면_콜백을_부른다(self):
            timer, clock = make_timer()
            fired = threading.Event()
            calls = []

            def on_expire(game_id, turn_seq):
                calls.append((game_id, turn_seq))
                fired.set()

            timer.schedule("g1", 3, clock.now_ms() + 30, on_expire)

            assert fired.wait(timeout=2)
            assert calls == [("g1", 3)]

        def test_성공_콜백_예외는_로그로_남기고_삼키지_않는다(self, caplog):
            timer, clock = make_timer()
            done = threading.Event()

            def on_expire(game_id, turn_seq):
                done.set()
                raise RuntimeError("boom")

            with caplog.at_level(logging.ERROR):
                timer.schedule("g1", 1, clock.now_ms(), on_expire)
                assert done.wait(timeout=2)
                for _ in range(50):
                    if "턴 만료 처리 실패" in caplog.text:
                        break
                    threading.Event().wait(0.02)

            assert "턴 만료 처리 실패" in caplog.text
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `cd server && .venv/bin/pytest tests/game/test_payloads.py tests/game/test_background_turn_timer.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'wheresmeow.game.adapter.outbound.socket'`

- [ ] **Step 3: 구현**

`server/src/wheresmeow/shared/socket_rooms.py`:

```python
def player_room(player_id: str) -> str:
    """플레이어의 모든 소켓 연결이 들어가는 Socket.IO 룸 이름. 탭을 여러 개 열어도 모두 받는다."""
    return f"player:{player_id}"
```

`server/src/wheresmeow/game/adapter/outbound/socket/payloads.py`:

```python
"""대국 도메인 객체를 클라이언트로 보내는 JSON 으로 바꾼다.

고양이 위치는 game:ended 에서만 내보낸다. 진행 중 페이로드에 board 를 넣지 말 것.
"""

from typing import Any

from wheresmeow.game.domain.game import CellsRevealed, Game, GameEnded, GameEvent, OpenedCell, TurnTimedOut


def cell_payload(cell: OpenedCell) -> dict[str, Any]:
    if cell.found_by is not None:
        return {"x": cell.x, "y": cell.y, "kind": "cat", "seat": cell.found_by}
    return {"x": cell.x, "y": cell.y, "kind": "number", "n": cell.number}


def started_payload(game: Game, my_seat: int) -> dict[str, Any]:
    return {
        "gameId": game.id,
        "mode": game.mode.value,
        "mySeat": my_seat,
        "seats": [{"nickname": s.nickname, "skin": s.skin, "score": s.score} for s in game.seats],
        "currentSeat": game.current_seat,
        "turnDeadline": game.turn_deadline_ms,
        "version": game.version,
        "cells": [cell_payload(c) for c in game.opened.values()],
    }


def event_payload(game_id: str, event: GameEvent) -> tuple[str, dict[str, Any]]:
    match event:
        case CellsRevealed():
            return "game:revealed", {
                "gameId": game_id,
                "seat": event.seat,
                "cells": [cell_payload(c) for c in event.cells],
                "scores": list(event.scores),
                "currentSeat": event.current_seat,
                "turnDeadline": event.turn_deadline_ms,
                "version": event.version,
            }
        case TurnTimedOut():
            return "game:timeout", {
                "gameId": game_id,
                "seat": event.seat,
                "scores": list(event.scores),
                "currentSeat": event.current_seat,
                "turnDeadline": event.turn_deadline_ms,
                "version": event.version,
            }
        case GameEnded():
            return "game:ended", {
                "gameId": game_id,
                "reason": event.reason.value,
                "winner": event.winner,
                "scores": list(event.scores),
                "cats": [[x, y] for x, y in event.cats],
                "version": event.version,
            }
    raise TypeError(f"알 수 없는 이벤트입니다: {event!r}")
```

`server/src/wheresmeow/game/adapter/outbound/socket/socketio_game_event_publisher.py`:

```python
from collections.abc import Sequence

from flask_socketio import SocketIO

from wheresmeow.game.adapter.outbound.socket.payloads import event_payload, started_payload
from wheresmeow.game.domain.game import Game, GameEvent
from wheresmeow.shared.socket_rooms import player_room


class SocketIOGameEventPublisher:
    """두 참가자의 player 룸으로 이벤트를 보낸다."""

    def __init__(self, socketio: SocketIO) -> None:
        self._socketio = socketio

    def game_started(self, game: Game) -> None:
        for index, seat in enumerate(game.seats):
            self._socketio.emit("game:started", started_payload(game, index), to=player_room(seat.player_id))

    def publish(self, game: Game, events: Sequence[GameEvent]) -> None:
        for event in events:
            name, payload = event_payload(game.id, event)
            for seat in game.seats:
                self._socketio.emit(name, payload, to=player_room(seat.player_id))
```

`server/src/wheresmeow/game/adapter/outbound/timer/background_turn_timer.py`:

```python
import logging
from collections.abc import Callable

from flask_socketio import SocketIO

from wheresmeow.shared.clock import Clock

logger = logging.getLogger(__name__)


class BackgroundTurnTimer:
    """Socket.IO 의 백그라운드 작업으로 턴 마감을 기다린다.

    async_mode 가 threading 이면 스레드, gevent 이면 greenlet 으로 동작한다.
    취소 기능은 없다. 지나간 턴의 만료는 Game.timeout 이 turn_seq 로 걸러 낸다.
    """

    def __init__(self, socketio: SocketIO, clock: Clock) -> None:
        self._socketio = socketio
        self._clock = clock

    def schedule(
        self,
        game_id: str,
        turn_seq: int,
        deadline_ms: int,
        on_expire: Callable[[str, int], None],
    ) -> None:
        self._socketio.start_background_task(self._run, game_id, turn_seq, deadline_ms, on_expire)

    def _run(self, game_id: str, turn_seq: int, deadline_ms: int, on_expire: Callable[[str, int], None]) -> None:
        self._socketio.sleep(max(0, deadline_ms - self._clock.now_ms()) / 1000)
        try:
            on_expire(game_id, turn_seq)
        except Exception:
            logger.exception("턴 만료 처리 실패 game_id=%s turn_seq=%s", game_id, turn_seq)
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `cd server && .venv/bin/pytest tests/game -v`
Expected: PASS (54 passed: board 7, skins 6, game 21, service 13, payloads 5, timer 2)

- [ ] **Step 5: 커밋**

```bash
git add server/src/wheresmeow/shared/socket_rooms.py server/src/wheresmeow/game/adapter server/tests/game
git commit -m "feat: 대국 이벤트 페이로드·소켓 발행·턴 타이머 어댑터 추가"
```

---

### Task 9: 앱 조립과 inbound 어댑터(REST, 소켓)

**Files:**
- Create: `server/src/wheresmeow/shared/payload.py`
- Create: `server/src/wheresmeow/game/adapter/inbound/socket/game_socket_handlers.py`
- Create: `server/src/wheresmeow/account/adapter/inbound/web/account_api.py`
- Create: `server/src/wheresmeow/room/adapter/inbound/web/room_api.py`
- Create: `server/src/wheresmeow/room/adapter/inbound/socket/room_socket_handlers.py`
- Create: `server/src/wheresmeow/room/adapter/outbound/account/account_player_directory.py`
- Create: `server/src/wheresmeow/room/adapter/outbound/game/game_starter_adapter.py`
- Create: `server/src/wheresmeow/bootstrap/config.py`
- Create: `server/src/wheresmeow/bootstrap/identity.py`
- Create: `server/src/wheresmeow/bootstrap/error_handlers.py`
- Create: `server/src/wheresmeow/bootstrap/container.py`
- Create: `server/src/wheresmeow/bootstrap/app_factory.py`
- Create: `server/src/wheresmeow/__main__.py`
- Test: `server/tests/integration_support.py`, `server/tests/conftest.py`
- Test: `server/tests/bootstrap/test_config.py`
- Test: `server/tests/account/integration/test_account_api.py`
- Test: `server/tests/room/integration/test_invite_game_flow.py`
- Test: `server/tests/game/integration/test_game_socket.py`

**Interfaces:**
- Consumes: Task 1~8의 모든 공개 이름
- Produces: `create_app(config: AppConfig | None = None, **overrides) -> tuple[Flask, SocketIO]` (overrides: `clock`, `turn_timer`, `layout_generator`, `first_seat_chooser`); `AppConfig(env, secret_key, test_seed, async_mode)`와 `AppConfig.from_env(environ)`; REST `POST /api/guests`, `GET /api/players/me`, `POST /api/rooms`, `GET /api/rooms/<code>`; 소켓 `connect(auth={"token"})`, `room:join`, `room:cancel`, `game:reveal`, `game:forfeit`, 서버 이벤트 `room:waiting`, `room:cancelled`, `game:started`, `game:revealed`, `game:timeout`, `game:ended`, `error`. 개발 서버는 `python -m wheresmeow`(포트 5000).

- [ ] **Step 1: 통합 테스트 도우미 작성**

통합 테스트는 가짜 시계, 가짜 타이머, 고정 배치(아래쪽 두 줄 + (11,9)), 항상 방장 선공으로 앱을 띄운다.

`server/tests/integration_support.py`:

```python
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
```

`server/tests/conftest.py`:

```python
import pytest

from integration_support import AppEnv, build_app_env


@pytest.fixture
def app_env() -> AppEnv:
    return build_app_env()
```

- [ ] **Step 2: 실패하는 테스트 작성**

`server/tests/bootstrap/test_config.py`:

```python
import pytest

from wheresmeow.bootstrap.config import AppConfig


class TestAppConfig:
    class TestFromEnv:
        def test_성공_환경_변수를_읽는다(self):
            config = AppConfig.from_env(
                {"WHERESMEOW_ENV": "test", "WHERESMEOW_SECRET_KEY": "s", "WHERESMEOW_TEST_SEED": "7"}
            )

            assert (config.env, config.secret_key, config.test_seed) == ("test", "s", 7)

        def test_성공_값이_없으면_개발_환경_기본값을_쓴다(self):
            config = AppConfig.from_env({})

            assert (config.env, config.test_seed, config.async_mode) == ("development", None, "threading")

    class TestValidate:
        def test_실패_운영_환경에_서명_키가_없으면_시작을_거부한다(self):
            with pytest.raises(ValueError):
                AppConfig.from_env({"WHERESMEOW_ENV": "production"})

        def test_실패_운영_환경에_테스트_시드가_켜져_있으면_시작을_거부한다(self):
            with pytest.raises(ValueError):
                AppConfig(env="production", secret_key="real-secret", test_seed=1)

        def test_실패_알_수_없는_환경이면_거부한다(self):
            with pytest.raises(ValueError):
                AppConfig(env="staging")
```

`server/tests/account/integration/test_account_api.py`:

```python
from integration_support import create_guest


class TestAccountApi:
    class TestPostGuests:
        def test_성공_게스트를_만들고_토큰과_플레이어를_돌려준다(self, app_env):
            response = app_env.http.post("/api/guests", json={"nickname": "고양이집사"})

            assert response.status_code == 201
            body = response.get_json()
            assert body["token"]
            assert body["player"]["nickname"] == "고양이집사"
            assert body["player"]["kind"] == "GUEST"
            assert (body["player"]["skin1p"], body["player"]["skin2p"]) == (16, 17)

        def test_실패_닉네임이_규칙에_맞지_않으면_400(self, app_env):
            response = app_env.http.post("/api/guests", json={"nickname": "냥"})

            assert response.status_code == 400
            assert response.get_json()["code"] == "INVALID_INPUT"

        def test_실패_본문이_없으면_400(self, app_env):
            response = app_env.http.post("/api/guests")

            assert response.status_code == 400
            assert response.get_json()["code"] == "INVALID_INPUT"

    class TestGetMe:
        def test_성공_토큰으로_내_정보를_조회한다(self, app_env):
            token, player_id = create_guest(app_env, "냥냥이")

            response = app_env.http.get("/api/players/me", headers={"Authorization": f"Bearer {token}"})

            assert response.status_code == 200
            assert response.get_json()["id"] == player_id

        def test_실패_토큰이_없으면_401(self, app_env):
            response = app_env.http.get("/api/players/me")

            assert response.status_code == 401
            assert response.get_json()["code"] == "UNAUTHORIZED"

        def test_실패_위조된_토큰이면_401(self, app_env):
            response = app_env.http.get("/api/players/me", headers={"Authorization": "Bearer forged"})

            assert response.status_code == 401
```

`server/tests/room/integration/test_invite_game_flow.py`:

```python
import pytest

from integration_support import connect, create_guest, received


@pytest.fixture
def started(app_env):
    """방장 A 와 손님 B 가 초대 방으로 대국을 시작한 상태."""
    token_a, _ = create_guest(app_env, "방장냥")
    token_b, _ = create_guest(app_env, "손님냥")
    code = app_env.http.post("/api/rooms", headers={"Authorization": f"Bearer {token_a}"}).get_json()["code"]
    a, b = connect(app_env, token_a), connect(app_env, token_b)
    a.emit("room:join", {"code": code})
    waiting = received(a, "room:waiting")
    b.emit("room:join", {"code": code})
    started_a, started_b = received(a, "game:started"), received(b, "game:started")
    return {
        "a": a,
        "b": b,
        "token_a": token_a,
        "code": code,
        "waiting": waiting,
        "started_a": started_a,
        "started_b": started_b,
    }


class TestInviteGameFlow:
    class TestStart:
        def test_성공_방장은_대기하고_상대가_오면_두_사람_모두_대국_시작을_받는다(self, started):
            assert started["waiting"][0]["code"] == started["code"]
            [game_a], [game_b] = started["started_a"], started["started_b"]
            assert game_a["gameId"] == game_b["gameId"]
            assert (game_a["mySeat"], game_b["mySeat"]) == (0, 1)
            assert [s["nickname"] for s in game_a["seats"]] == ["방장냥", "손님냥"]

        def test_성공_1P가_겹치면_손님이_2P_스킨을_쓴다(self, started):
            [game] = started["started_a"]

            assert [s["skin"] for s in game["seats"]] == [16, 17]

        def test_성공_시작_페이로드에_고양이_위치가_없다(self, started):
            [game] = started["started_b"]

            assert "cats" not in game
            assert game["cells"] == []

    class TestPlay:
        def test_성공_고양이를_찾고_빈_칸을_열고_기권까지_진행한다(self, started):
            a, b = started["a"], started["b"]
            game_id = started["started_a"][0]["gameId"]

            a.emit("game:reveal", {"gameId": game_id, "x": 11, "y": 9})
            a.emit("game:reveal", {"gameId": game_id, "x": 0, "y": 0})
            b.emit("game:forfeit", {"gameId": game_id})

            revealed = received(b, "game:revealed")
            assert revealed[0]["cells"] == [{"x": 11, "y": 9, "kind": "cat", "seat": 0}]
            assert revealed[0]["currentSeat"] == 0
            assert len(revealed[1]["cells"]) > 1
            assert revealed[1]["currentSeat"] == 1
            [ended] = received(a, "game:ended")
            assert (ended["reason"], ended["winner"], ended["version"]) == ("FORFEIT", 0, 3)
            assert len(ended["cats"]) == 25

        def test_성공_턴_시간이_지나면_두_사람_모두_감점_이벤트를_받는다(self, app_env, started):
            app_env.timer.fire_latest()

            [timeout_a] = received(started["a"], "game:timeout")
            [timeout_b] = received(started["b"], "game:timeout")
            assert timeout_a == timeout_b
            assert (timeout_a["scores"], timeout_a["currentSeat"]) == ([-1, 0], 1)

        def test_성공_같은_플레이어가_탭을_두_개_열면_두_탭_모두_이벤트를_받는다(self, app_env, started):
            token_a = started["token_a"]
            second_tab = connect(app_env, token_a)
            game_id = started["started_a"][0]["gameId"]

            started["a"].emit("game:reveal", {"gameId": game_id, "x": 11, "y": 9})

            assert len(received(second_tab, "game:revealed")) == 1

        def test_실패_자기_차례가_아니면_요청한_사람만_오류를_받는다(self, started):
            a, b = started["a"], started["b"]
            game_id = started["started_a"][0]["gameId"]

            b.emit("game:reveal", {"gameId": game_id, "x": 0, "y": 0})

            assert [e["code"] for e in received(b, "error")] == ["NOT_YOUR_TURN"]
            assert received(a, "error") == []

        def test_실패_대국이_시작된_방에_세_번째_사람이_오면_오류를_받는다(self, app_env, started):
            token_c, _ = create_guest(app_env, "구경냥")
            c = connect(app_env, token_c)

            c.emit("room:join", {"code": started["code"]})

            assert [e["code"] for e in received(c, "error")] == ["ROOM_FULL"]


class TestRoomApi:
    class TestGetRoom:
        def test_성공_방_상태를_조회한다(self, app_env):
            token, _ = create_guest(app_env, "방장냥")
            code = app_env.http.post("/api/rooms", headers={"Authorization": f"Bearer {token}"}).get_json()["code"]

            response = app_env.http.get(f"/api/rooms/{code}")

            assert response.status_code == 200
            assert response.get_json()["status"] == "WAITING"

        def test_실패_없는_방이면_404(self, app_env):
            response = app_env.http.get("/api/rooms/ZZZZZZ")

            assert response.status_code == 404
            assert response.get_json()["code"] == "ROOM_NOT_FOUND"

    class TestPostRoom:
        def test_실패_토큰이_없으면_401(self, app_env):
            assert app_env.http.post("/api/rooms").status_code == 401

    class TestJoinSocket:
        def test_실패_없는_방_코드면_오류를_받는다(self, app_env):
            token, _ = create_guest(app_env, "길잃은냥")
            client = connect(app_env, token)

            client.emit("room:join", {"code": "ZZZZZZ"})

            assert [e["code"] for e in received(client, "error")] == ["ROOM_NOT_FOUND"]
```

`server/tests/game/integration/test_game_socket.py`:

```python
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
```

- [ ] **Step 3: 테스트가 실패하는지 확인**

Run: `cd server && .venv/bin/pytest -v`
Expected: FAIL — 수집 단계에서 `ModuleNotFoundError: No module named 'wheresmeow.bootstrap'`

- [ ] **Step 4: 입력 검증 도우미와 inbound 어댑터 작성**

`server/src/wheresmeow/shared/payload.py`:

```python
"""inbound 어댑터가 요청 본문을 pydantic 스키마로 검증할 때 쓰는 도우미."""

from typing import Any

from pydantic import BaseModel, ValidationError

from wheresmeow.shared.errors import InvalidInput


def parse_payload[M: BaseModel](model: type[M], data: Any) -> M:
    try:
        return model.model_validate(data if data is not None else {})
    except ValidationError as error:
        raise InvalidInput(error.errors(include_url=False)[0]["msg"]) from error
```

`server/src/wheresmeow/game/adapter/inbound/socket/game_socket_handlers.py`:

```python
from collections.abc import Callable

from flask_socketio import SocketIO
from pydantic import BaseModel, ConfigDict, Field, StrictInt

from wheresmeow.game.application.port.inbound import ForfeitUseCase, RevealCellUseCase
from wheresmeow.shared.payload import parse_payload


class RevealRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    gameId: str = Field(min_length=1)
    x: StrictInt
    y: StrictInt


class GameRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    gameId: str = Field(min_length=1)


def register_game_socket_handlers(
    socketio: SocketIO,
    reveal: RevealCellUseCase,
    forfeit: ForfeitUseCase,
    current_player_id: Callable[[], str],
) -> None:
    """결과는 GameEventPublisher 가 두 참가자에게 보낸다. 실패는 공통 오류 핸들러가 error 로 보낸다."""

    @socketio.on("game:reveal")
    def on_reveal(data):
        request = parse_payload(RevealRequest, data)
        reveal.reveal(request.gameId, current_player_id(), request.x, request.y)

    @socketio.on("game:forfeit")
    def on_forfeit(data):
        request = parse_payload(GameRequest, data)
        forfeit.forfeit(request.gameId, current_player_id())
```

`server/src/wheresmeow/account/adapter/inbound/web/account_api.py`:

```python
from collections.abc import Callable
from typing import Any

from flask import Blueprint, jsonify, request
from pydantic import BaseModel, ConfigDict

from wheresmeow.account.application.port.inbound import CreateGuestUseCase
from wheresmeow.account.domain.player import Player
from wheresmeow.shared.payload import parse_payload


class CreateGuestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nickname: str


def player_payload(player: Player) -> dict[str, Any]:
    return {
        "id": player.id,
        "kind": player.kind.value,
        "nickname": player.nickname,
        "skin1p": player.skin_1p,
        "skin2p": player.skin_2p,
    }


def create_account_blueprint(
    create_guest: CreateGuestUseCase,
    current_player: Callable[[], Player],
) -> Blueprint:
    blueprint = Blueprint("account", __name__, url_prefix="/api")

    @blueprint.post("/guests")
    def post_guest():
        body = parse_payload(CreateGuestRequest, request.get_json(silent=True))
        credentials = create_guest.create_guest(body.nickname)
        return jsonify({"token": credentials.token, "player": player_payload(credentials.player)}), 201

    @blueprint.get("/players/me")
    def get_me():
        return jsonify(player_payload(current_player()))

    return blueprint
```

`server/src/wheresmeow/room/adapter/inbound/web/room_api.py`:

```python
from collections.abc import Callable
from typing import Any

from flask import Blueprint, jsonify

from wheresmeow.room.application.port.inbound import CreateRoomUseCase, GetRoomUseCase
from wheresmeow.room.domain.room import Room


def room_payload(room: Room) -> dict[str, Any]:
    return {"code": room.code, "status": room.status.value, "expiresAt": room.expires_at_ms}


def create_room_blueprint(
    create_room: CreateRoomUseCase,
    get_room: GetRoomUseCase,
    current_player_id: Callable[[], str],
) -> Blueprint:
    blueprint = Blueprint("room", __name__, url_prefix="/api/rooms")

    @blueprint.post("")
    def post_room():
        return jsonify(room_payload(create_room.create_room(current_player_id()))), 201

    @blueprint.get("/<code>")
    def get_room_by_code(code: str):
        return jsonify(room_payload(get_room.get_room(code)))

    return blueprint
```

`server/src/wheresmeow/room/adapter/inbound/socket/room_socket_handlers.py`:

```python
from collections.abc import Callable

from flask_socketio import SocketIO, emit
from pydantic import BaseModel, ConfigDict, Field

from wheresmeow.room.adapter.inbound.web.room_api import room_payload
from wheresmeow.room.application.port.inbound import CancelRoomUseCase, JoinRoomUseCase
from wheresmeow.shared.payload import parse_payload


class RoomRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str = Field(min_length=6, max_length=6)


def register_room_socket_handlers(
    socketio: SocketIO,
    join_room: JoinRoomUseCase,
    cancel_room: CancelRoomUseCase,
    current_player_id: Callable[[], str],
) -> None:
    @socketio.on("room:join")
    def on_join(data):
        request = parse_payload(RoomRequest, data)
        outcome = join_room.join(request.code, current_player_id())
        if outcome.game_id is None:
            emit("room:waiting", room_payload(outcome.room))
        # 대국이 시작되면 game:started 는 GameEventPublisher 가 두 사람에게 보낸다

    @socketio.on("room:cancel")
    def on_cancel(data):
        request = parse_payload(RoomRequest, data)
        cancel_room.cancel(request.code, current_player_id())
        emit("room:cancelled", {"code": request.code.upper()})
```

- [ ] **Step 5: 도메인 간 outbound 어댑터 작성**

room 도메인은 account와 game을 직접 import하지 않고, 이 두 어댑터를 통해서만 부른다.

`server/src/wheresmeow/room/adapter/outbound/account/account_player_directory.py`:

```python
from wheresmeow.account.application.port.inbound import GetPlayerUseCase
from wheresmeow.room.application.port.outbound import PlayerProfile


class AccountPlayerDirectory:
    """room 의 PlayerDirectory 포트를 account 의 GetPlayer 유스케이스로 구현한다."""

    def __init__(self, get_player: GetPlayerUseCase) -> None:
        self._get_player = get_player

    def profile(self, player_id: str) -> PlayerProfile:
        player = self._get_player.get_player(player_id)
        return PlayerProfile(player.id, player.nickname, player.skin_1p, player.skin_2p)
```

`server/src/wheresmeow/room/adapter/outbound/game/game_starter_adapter.py`:

```python
from wheresmeow.game.application.port.inbound import GamePlayer, StartGameUseCase
from wheresmeow.game.domain.game import GameMode
from wheresmeow.game.domain.skins import SkinPreference
from wheresmeow.room.application.port.outbound import PlayerProfile


class GameStarterAdapter:
    """room 의 GameStarter 포트를 game 의 StartGame 유스케이스로 구현한다."""

    def __init__(self, start_game: StartGameUseCase) -> None:
        self._start_game = start_game

    def start_invite_game(self, host: PlayerProfile, guest: PlayerProfile) -> str:
        game = self._start_game.start_game(GameMode.INVITE, self._to_player(host), self._to_player(guest))
        return game.id

    @staticmethod
    def _to_player(profile: PlayerProfile) -> GamePlayer:
        return GamePlayer(profile.player_id, profile.nickname, SkinPreference(profile.skin_1p, profile.skin_2p))
```

- [ ] **Step 6: bootstrap 작성**

`server/src/wheresmeow/bootstrap/config.py`:

```python
import os
from collections.abc import Mapping
from dataclasses import dataclass

DEV_SECRET_KEY = "dev-only-secret"


@dataclass(frozen=True)
class AppConfig:
    env: str = "development"  # development · test · production
    secret_key: str = DEV_SECRET_KEY
    test_seed: int | None = None
    async_mode: str = "threading"  # 운영은 gevent

    def __post_init__(self) -> None:
        if self.env not in ("development", "test", "production"):
            raise ValueError(f"알 수 없는 실행 환경입니다: {self.env}")
        if self.env == "production":
            if self.secret_key == DEV_SECRET_KEY or not self.secret_key:
                raise ValueError("운영 환경에는 WHERESMEOW_SECRET_KEY 가 필요합니다")
            if self.test_seed is not None:
                raise ValueError("운영 환경에서 WHERESMEOW_TEST_SEED 를 켤 수 없습니다")

    @classmethod
    def from_env(cls, environ: Mapping[str, str] = os.environ) -> "AppConfig":
        seed = environ.get("WHERESMEOW_TEST_SEED")
        return cls(
            env=environ.get("WHERESMEOW_ENV", "development"),
            secret_key=environ.get("WHERESMEOW_SECRET_KEY", DEV_SECRET_KEY),
            test_seed=int(seed) if seed else None,
            async_mode=environ.get("WHERESMEOW_ASYNC_MODE", "threading"),
        )
```

`server/src/wheresmeow/bootstrap/identity.py`:

```python
"""요청을 보낸 플레이어를 알아내는 방법. HTTP 는 Bearer 토큰, 소켓은 연결 시 등록한 sid."""

import threading

from flask import request

from wheresmeow.account.application.port.inbound import AuthenticateUseCase
from wheresmeow.account.domain.player import Player
from wheresmeow.shared.errors import Unauthorized


class HttpIdentity:
    def __init__(self, authenticate: AuthenticateUseCase) -> None:
        self._authenticate = authenticate

    def current_player(self) -> Player:
        header = request.headers.get("Authorization", "")
        scheme, _, token = header.partition(" ")
        if scheme != "Bearer" or not token:
            raise Unauthorized("Authorization: Bearer <토큰> 헤더가 필요합니다")
        return self._authenticate.authenticate(token)

    def current_player_id(self) -> str:
        return self.current_player().id


class SocketSessions:
    def __init__(self) -> None:
        self._players: dict[str, str] = {}
        self._guard = threading.Lock()

    def bind(self, sid: str, player_id: str) -> None:
        with self._guard:
            self._players[sid] = player_id

    def unbind(self, sid: str) -> None:
        with self._guard:
            self._players.pop(sid, None)

    def current_player_id(self) -> str:
        with self._guard:
            player_id = self._players.get(request.sid)
        if player_id is None:
            raise Unauthorized("인증되지 않은 소켓 연결입니다")
        return player_id
```

`server/src/wheresmeow/bootstrap/error_handlers.py`:

```python
import logging

from flask import Flask, jsonify
from flask_socketio import SocketIO, emit
from werkzeug.exceptions import HTTPException

from wheresmeow.shared.errors import DomainError

logger = logging.getLogger(__name__)

HTTP_STATUS_BY_CODE = {
    "INVALID_INPUT": 400,
    "UNAUTHORIZED": 401,
    "NOT_A_PARTICIPANT": 403,
    "NOT_ROOM_HOST": 403,
    "GAME_NOT_FOUND": 404,
    "ROOM_NOT_FOUND": 404,
    "PLAYER_NOT_FOUND": 404,
    "ALREADY_IN_GAME": 409,
    "ROOM_FULL": 409,
    "ROOM_EXPIRED": 410,
}


def error_body(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def register_http_error_handlers(app: Flask) -> None:
    @app.errorhandler(DomainError)
    def on_domain_error(error: DomainError):
        return jsonify(error_body(error.code, error.message)), HTTP_STATUS_BY_CODE.get(error.code, 400)

    @app.errorhandler(Exception)
    def on_unexpected(error: Exception):
        if isinstance(error, HTTPException):
            return error
        logger.exception("처리하지 못한 HTTP 예외")
        return jsonify(error_body("INTERNAL", "서버 오류가 발생했습니다")), 500


def register_socket_error_handler(socketio: SocketIO) -> None:
    @socketio.on_error_default
    def on_error(error: Exception):
        if isinstance(error, DomainError):
            emit("error", error_body(error.code, error.message))
            return
        logger.exception("처리하지 못한 소켓 예외")
        emit("error", error_body("INTERNAL", "서버 오류가 발생했습니다"))
```

`server/src/wheresmeow/bootstrap/container.py`:

```python
"""어댑터를 포트에 연결한다. 테스트는 키워드 인자로 일부 어댑터를 바꿔 끼운다."""

from collections.abc import Callable
from dataclasses import dataclass

from flask_socketio import SocketIO

from wheresmeow.account.adapter.outbound.memory.in_memory_player_store import InMemoryPlayerStore
from wheresmeow.account.adapter.outbound.token.signed_token_issuer import SignedTokenIssuer
from wheresmeow.account.application.service.guest_service import GuestService
from wheresmeow.bootstrap.config import AppConfig
from wheresmeow.bootstrap.identity import HttpIdentity, SocketSessions
from wheresmeow.game.adapter.outbound.memory.in_memory_game_store import InMemoryGameStore
from wheresmeow.game.adapter.outbound.socket.socketio_game_event_publisher import SocketIOGameEventPublisher
from wheresmeow.game.adapter.outbound.timer.background_turn_timer import BackgroundTurnTimer
from wheresmeow.game.application.port.outbound import TurnTimer
from wheresmeow.game.application.service.game_service import GameService
from wheresmeow.game.domain.board import MineLayoutGenerator, RandomMineLayoutGenerator, SeededMineLayoutGenerator
from wheresmeow.room.adapter.outbound.account.account_player_directory import AccountPlayerDirectory
from wheresmeow.room.adapter.outbound.game.game_starter_adapter import GameStarterAdapter
from wheresmeow.room.adapter.outbound.memory.in_memory_room_store import InMemoryRoomStore
from wheresmeow.room.application.service.room_service import RoomService
from wheresmeow.shared.clock import Clock, SystemClock


@dataclass(frozen=True)
class Container:
    config: AppConfig
    guest_service: GuestService
    game_service: GameService
    room_service: RoomService
    http_identity: HttpIdentity
    socket_sessions: SocketSessions


def build_container(
    config: AppConfig,
    socketio: SocketIO,
    *,
    clock: Clock | None = None,
    turn_timer: TurnTimer | None = None,
    layout_generator: MineLayoutGenerator | None = None,
    first_seat_chooser: Callable[[], int] | None = None,
) -> Container:
    clock = clock or SystemClock()
    if layout_generator is None:
        layout_generator = (
            SeededMineLayoutGenerator(config.test_seed)
            if config.test_seed is not None
            else RandomMineLayoutGenerator()
        )

    guest_service = GuestService(InMemoryPlayerStore(), SignedTokenIssuer(config.secret_key))

    game_options = {"first_seat_chooser": first_seat_chooser} if first_seat_chooser else {}
    game_service = GameService(
        InMemoryGameStore(),
        SocketIOGameEventPublisher(socketio),
        turn_timer or BackgroundTurnTimer(socketio, clock),
        layout_generator,
        clock,
        **game_options,
    )

    room_service = RoomService(
        InMemoryRoomStore(),
        AccountPlayerDirectory(guest_service),
        GameStarterAdapter(game_service),
        clock,
    )

    return Container(
        config=config,
        guest_service=guest_service,
        game_service=game_service,
        room_service=room_service,
        http_identity=HttpIdentity(guest_service),
        socket_sessions=SocketSessions(),
    )
```

`server/src/wheresmeow/bootstrap/app_factory.py`:

```python
from flask import Flask, request
from flask_socketio import ConnectionRefusedError, SocketIO, join_room

from wheresmeow.account.adapter.inbound.web.account_api import create_account_blueprint
from wheresmeow.bootstrap.config import AppConfig
from wheresmeow.bootstrap.container import Container, build_container
from wheresmeow.bootstrap.error_handlers import register_http_error_handlers, register_socket_error_handler
from wheresmeow.game.adapter.inbound.socket.game_socket_handlers import register_game_socket_handlers
from wheresmeow.room.adapter.inbound.socket.room_socket_handlers import register_room_socket_handlers
from wheresmeow.room.adapter.inbound.web.room_api import create_room_blueprint
from wheresmeow.shared.errors import DomainError
from wheresmeow.shared.socket_rooms import player_room


def create_app(config: AppConfig | None = None, **overrides) -> tuple[Flask, SocketIO]:
    """overrides 는 build_container 의 키워드 인자(clock, turn_timer 등)로 그대로 전달된다."""
    config = config or AppConfig.from_env()
    app = Flask(__name__)
    app.config["SECRET_KEY"] = config.secret_key
    socketio = SocketIO(app, async_mode=config.async_mode)

    container = build_container(config, socketio, **overrides)
    app.extensions["wheresmeow"] = container

    register_http_error_handlers(app)
    register_socket_error_handler(socketio)
    _register_connection_handlers(socketio, container)

    identity = container.http_identity
    app.register_blueprint(create_account_blueprint(container.guest_service, identity.current_player))
    app.register_blueprint(
        create_room_blueprint(container.room_service, container.room_service, identity.current_player_id)
    )

    sessions = container.socket_sessions
    register_room_socket_handlers(
        socketio, container.room_service, container.room_service, sessions.current_player_id
    )
    register_game_socket_handlers(
        socketio, container.game_service, container.game_service, sessions.current_player_id
    )
    return app, socketio


def _register_connection_handlers(socketio: SocketIO, container: Container) -> None:
    @socketio.on("connect")
    def on_connect(auth):
        token = auth.get("token") if isinstance(auth, dict) else None
        try:
            player = container.guest_service.authenticate(token or "")
        except DomainError as error:
            raise ConnectionRefusedError(error.code) from error
        container.socket_sessions.bind(request.sid, player.id)
        join_room(player_room(player.id))

    @socketio.on("disconnect")
    def on_disconnect(*_args):
        container.socket_sessions.unbind(request.sid)
```

`server/src/wheresmeow/__main__.py`:

```python
"""개발 서버: python -m wheresmeow (기본 포트 5000)."""

import logging
import os

from wheresmeow.bootstrap.app_factory import create_app

logging.basicConfig(level=logging.INFO)
app, socketio = create_app()

if __name__ == "__main__":
    socketio.run(app, host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), allow_unsafe_werkzeug=True)
```

- [ ] **Step 7: 전체 서버 테스트 통과 확인**

Run: `cd server && .venv/bin/pytest`
Expected: PASS (109 passed)

- [ ] **Step 8: 개발 서버 동작 확인**

Run: `cd server && .venv/bin/python -m wheresmeow` (다른 터미널에서 아래 명령 실행 후 Ctrl+C로 종료)

Run: `curl -s -X POST http://127.0.0.1:5000/api/guests -H 'Content-Type: application/json' -d '{"nickname":"테스트냥"}'`
Expected: `{"player":{"id":"...","kind":"GUEST",...,"skin1p":16,"skin2p":17},"token":"..."}`

- [ ] **Step 9: 커밋**

```bash
git add server
git commit -m "feat: 앱 조립과 게스트·방·대국 REST·소켓 어댑터 추가"
```

---

### Task 10: 웹 골격, 대국 리듀서, 세션

**Files:**
- Create: `web/package.json`, `web/vite.config.ts`, `web/tsconfig.json`, `web/index.html`
- Create: `web/src/game/types.ts`
- Create: `web/src/game/gameReducer.ts`
- Create: `web/src/game/cellSize.ts`
- Create: `web/src/api/http.ts`
- Create: `web/src/session/sessionStore.ts`
- Test: `web/src/game/gameReducer.test.ts`, `web/src/game/cellSize.test.ts`, `web/src/session/sessionStore.test.ts`

**Interfaces:**
- Consumes: 서버 페이로드 형식 (Task 8 `payloads.py`), REST `POST /api/guests`, `GET /api/players/me` (Task 9)
- Produces: 타입 `SeatIndex`, `CellPayload`, `StartedPayload`, `RevealedPayload`, `TimeoutPayload`, `EndedPayload`, `Cell`, `GameState`, `GameAction`, `cellKey(x, y)`; `gameReducer(state, action)`; `BOARD_SIZE`, `computeCellSize(viewportWidth)`; `ApiError(code, message, status)`, `api<T>(path, {method, body, token})`; `Player`, `useSession`(token·player·setSession·clear), `createGuest(nickname)`, `verifySession()`.

- [ ] **Step 1: 프로젝트 설정 파일 작성**

`web/package.json`:

```json
{
  "name": "wheresmeow-web",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc --noEmit && vite build",
    "test": "vitest run"
  },
  "dependencies": {
    "react": "19.3.0",
    "react-dom": "19.3.0",
    "react-router": "8.4.0",
    "socket.io-client": "4.8.4",
    "zustand": "5.0.15"
  },
  "devDependencies": {
    "@testing-library/react": "16.3.3",
    "@types/react": "19.3.0",
    "@types/react-dom": "19.3.0",
    "@vitejs/plugin-react": "6.1.2",
    "jsdom": "30.1.2",
    "typescript": "7.0.2",
    "vite": "8.3.4",
    "vitest": "5.0.3"
  }
}
```

`web/vite.config.ts`:

```ts
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// 개발 중에는 Flask 개발 서버(5000)로 API 와 Socket.IO 를 넘긴다.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://127.0.0.1:5000",
      "/socket.io": { target: "http://127.0.0.1:5000", ws: true },
    },
  },
  test: {
    environment: "jsdom",
  },
});
```

`web/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "skipLibCheck": true,
    "isolatedModules": true,
    "types": ["vite/client"]
  },
  "include": ["src", "vite.config.ts"]
}
```

`web/index.html`:

```html
<!doctype html>
<html lang="ko">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
    <title>Where's Meow</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 2: 의존성 설치**

Run: `cd web && npm install`
Expected: `added ... packages`

- [ ] **Step 3: 실패하는 테스트 작성**

`web/src/game/gameReducer.test.ts`:

```ts
import { describe, expect, it } from "vitest";
import { gameReducer } from "./gameReducer";
import type { GameState, StartedPayload } from "./types";

const started: StartedPayload = {
  gameId: "g1",
  mode: "INVITE",
  mySeat: 1,
  seats: [
    { nickname: "방장냥", skin: 16, score: 0 },
    { nickname: "손님냥", skin: 17, score: 0 },
  ],
  currentSeat: 0,
  turnDeadline: 20_000,
  version: 0,
  cells: [],
};

const start = (): GameState => gameReducer(null, { type: "started", payload: started })!;

describe("gameReducer", () => {
  describe("started", () => {
    it("[성공] 시작 페이로드로 새 상태를 만든다", () => {
      const state = start();

      expect(state.mySeat).toBe(1);
      expect(state.status).toBe("IN_PROGRESS");
      expect(state.cells).toEqual({});
    });
  });

  describe("revealed", () => {
    it("[성공] 열린 칸과 점수, 다음 턴을 반영한다", () => {
      const state = gameReducer(start(), {
        type: "revealed",
        payload: {
          gameId: "g1",
          seat: 0,
          cells: [
            { x: 3, y: 4, kind: "cat", seat: 0 },
            { x: 0, y: 0, kind: "number", n: 2 },
          ],
          scores: [1, 0],
          currentSeat: 0,
          turnDeadline: 40_000,
          version: 1,
        },
      })!;

      expect(state.cells["3,4"]).toEqual({ kind: "cat", seat: 0 });
      expect(state.cells["0,0"]).toEqual({ kind: "number", n: 2 });
      expect(state.seats[0].score).toBe(1);
      expect(state.turnDeadline).toBe(40_000);
      expect(state.version).toBe(1);
    });

    it("[실패] version 이 건너뛰면 적용하지 않고 outOfSync 로 표시한다", () => {
      const before = start();

      const state = gameReducer(before, {
        type: "revealed",
        payload: { gameId: "g1", seat: 0, cells: [], scores: [5, 5], currentSeat: 1, turnDeadline: 1, version: 2 },
      })!;

      expect(state.outOfSync).toBe(true);
      expect(state.seats[0].score).toBe(0);
      expect(state.version).toBe(0);
    });

    it("[실패] 다른 대국의 이벤트는 무시한다", () => {
      const before = start();

      const state = gameReducer(before, {
        type: "revealed",
        payload: { gameId: "other", seat: 0, cells: [], scores: [1, 0], currentSeat: 1, turnDeadline: 1, version: 1 },
      });

      expect(state).toBe(before);
    });
  });

  describe("timeout", () => {
    it("[성공] 감점과 턴 넘김을 반영한다", () => {
      const state = gameReducer(start(), {
        type: "timeout",
        payload: { gameId: "g1", seat: 0, scores: [-1, 0], currentSeat: 1, turnDeadline: 60_000, version: 1 },
      })!;

      expect(state.seats[0].score).toBe(-1);
      expect(state.currentSeat).toBe(1);
    });
  });

  describe("ended", () => {
    it("[성공] 결과를 기록하고 아무도 못 찾은 고양이를 공개한다", () => {
      const afterReveal = gameReducer(start(), {
        type: "revealed",
        payload: {
          gameId: "g1",
          seat: 0,
          cells: [{ x: 1, y: 1, kind: "cat", seat: 0 }],
          scores: [1, 0],
          currentSeat: 0,
          turnDeadline: 1,
          version: 1,
        },
      });

      const state = gameReducer(afterReveal, {
        type: "ended",
        payload: { gameId: "g1", reason: "FORFEIT", winner: 0, scores: [1, 0], cats: [[1, 1], [2, 2]], version: 2 },
      })!;

      expect(state.status).toBe("FINISHED");
      expect(state.result).toEqual({ reason: "FORFEIT", winner: 0 });
      expect(state.cells["1,1"]).toEqual({ kind: "cat", seat: 0 });
      expect(state.cells["2,2"]).toEqual({ kind: "cat", seat: null });
      expect(state.turnDeadline).toBeNull();
    });
  });
});
```

`web/src/game/cellSize.test.ts`:

```ts
import { describe, expect, it } from "vitest";
import { computeCellSize } from "./cellSize";

describe("computeCellSize", () => {
  it("[성공] 폭 360px 폰에서는 28px 이다", () => {
    expect(computeCellSize(360)).toBe(28);
  });

  it("[성공] 넓은 화면에서는 40px 로 제한한다", () => {
    expect(computeCellSize(1440)).toBe(40);
  });

  it("[성공] 폭 320px 작은 폰에서도 칸이 화면 안에 들어간다", () => {
    expect(computeCellSize(320) * 12).toBeLessThanOrEqual(320 - 24);
  });
});
```

`web/src/session/sessionStore.test.ts`:

```ts
import { afterEach, describe, expect, it, vi } from "vitest";
import { useSession, verifySession } from "./sessionStore";

const player = { id: "p1", kind: "GUEST" as const, nickname: "냥냥이", skin1p: 16, skin2p: 17 };

function mockFetch(status: number, body: unknown) {
  vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(body), { status })));
}

afterEach(() => {
  vi.unstubAllGlobals();
  useSession.getState().clear();
});

describe("verifySession", () => {
  it("[성공] 서버가 토큰을 받아 주면 세션을 유지한다", async () => {
    useSession.getState().setSession("token", player);
    mockFetch(200, player);

    await verifySession();

    expect(useSession.getState().token).toBe("token");
  });

  it("[성공] 서버 재시작 등으로 토큰이 거부되면(401) 세션을 지운다", async () => {
    useSession.getState().setSession("stale", player);
    mockFetch(401, { code: "UNAUTHORIZED", message: "" });

    await verifySession();

    expect(useSession.getState().token).toBeNull();
    expect(useSession.getState().player).toBeNull();
  });

  it("[실패] 401 이 아닌 오류는 세션을 지우지 않고 그대로 던진다", async () => {
    useSession.getState().setSession("token", player);
    mockFetch(500, { code: "INTERNAL", message: "" });

    await expect(verifySession()).rejects.toThrow();
    expect(useSession.getState().token).toBe("token");
  });
});
```

- [ ] **Step 4: 테스트가 실패하는지 확인**

Run: `cd web && npx vitest run`
Expected: FAIL — `Failed to resolve import "./gameReducer"` 등 3개 파일 모두 실패

- [ ] **Step 5: 구현**

`web/src/game/types.ts`:

```ts
// 서버 Socket.IO 페이로드와 1:1 로 대응한다 (server/.../game/adapter/outbound/socket/payloads.py).

export type SeatIndex = 0 | 1;

export type CellPayload =
  | { x: number; y: number; kind: "number"; n: number }
  | { x: number; y: number; kind: "cat"; seat: SeatIndex };

export interface SeatPayload {
  nickname: string;
  skin: number;
  score: number;
}

export interface StartedPayload {
  gameId: string;
  mode: "INVITE" | "MATCH" | "BOT";
  mySeat: SeatIndex;
  seats: [SeatPayload, SeatPayload];
  currentSeat: SeatIndex;
  turnDeadline: number | null;
  version: number;
  cells: CellPayload[];
}

export interface RevealedPayload {
  gameId: string;
  seat: SeatIndex;
  cells: CellPayload[];
  scores: [number, number];
  currentSeat: SeatIndex;
  turnDeadline: number | null;
  version: number;
}

export interface TimeoutPayload {
  gameId: string;
  seat: SeatIndex;
  scores: [number, number];
  currentSeat: SeatIndex;
  turnDeadline: number | null;
  version: number;
}

export type EndReason = "ALL_FOUND" | "FORFEIT" | "AUTO_FORFEIT";

export interface EndedPayload {
  gameId: string;
  reason: EndReason;
  winner: SeatIndex | null;
  scores: [number, number];
  cats: [number, number][];
  version: number;
}

// 화면 상태

export type Cell =
  | { kind: "number"; n: number }
  | { kind: "cat"; seat: SeatIndex | null }; // seat null = 끝난 뒤 공개된, 아무도 못 찾은 고양이

export interface GameState {
  gameId: string;
  mode: StartedPayload["mode"];
  mySeat: SeatIndex;
  seats: [SeatPayload, SeatPayload];
  currentSeat: SeatIndex;
  turnDeadline: number | null;
  version: number;
  cells: Record<string, Cell>;
  status: "IN_PROGRESS" | "FINISHED";
  result: { reason: EndReason; winner: SeatIndex | null } | null;
  outOfSync: boolean; // version 이 건너뛰었다. 2단계에서 game:sync 로 복구한다
}

export type GameAction =
  | { type: "started"; payload: StartedPayload }
  | { type: "revealed"; payload: RevealedPayload }
  | { type: "timeout"; payload: TimeoutPayload }
  | { type: "ended"; payload: EndedPayload };

export const cellKey = (x: number, y: number) => `${x},${y}`;
```

`web/src/game/gameReducer.ts`:

```ts
import { cellKey, type Cell, type CellPayload, type GameAction, type GameState } from "./types";

function toCell(payload: CellPayload): Cell {
  return payload.kind === "cat" ? { kind: "cat", seat: payload.seat } : { kind: "number", n: payload.n };
}

function withCells(cells: Record<string, Cell>, added: CellPayload[]): Record<string, Cell> {
  const next = { ...cells };
  for (const cell of added) next[cellKey(cell.x, cell.y)] = toCell(cell);
  return next;
}

function withScores(state: GameState, scores: [number, number]): GameState["seats"] {
  return [
    { ...state.seats[0], score: scores[0] },
    { ...state.seats[1], score: scores[1] },
  ];
}

/** 서버 이벤트를 version 순서대로만 적용한다. 순서가 어긋나면 적용하지 않고 outOfSync 로 표시한다. */
export function gameReducer(state: GameState | null, action: GameAction): GameState | null {
  if (action.type === "started") {
    const p = action.payload;
    return {
      gameId: p.gameId,
      mode: p.mode,
      mySeat: p.mySeat,
      seats: p.seats,
      currentSeat: p.currentSeat,
      turnDeadline: p.turnDeadline,
      version: p.version,
      cells: withCells({}, p.cells),
      status: "IN_PROGRESS",
      result: null,
      outOfSync: false,
    };
  }
  if (!state || action.payload.gameId !== state.gameId) return state;
  if (action.payload.version !== state.version + 1) return { ...state, outOfSync: true };

  switch (action.type) {
    case "revealed": {
      const p = action.payload;
      return {
        ...state,
        cells: withCells(state.cells, p.cells),
        seats: withScores(state, p.scores),
        currentSeat: p.currentSeat,
        turnDeadline: p.turnDeadline,
        version: p.version,
      };
    }
    case "timeout": {
      const p = action.payload;
      return {
        ...state,
        seats: withScores(state, p.scores),
        currentSeat: p.currentSeat,
        turnDeadline: p.turnDeadline,
        version: p.version,
      };
    }
    case "ended": {
      const p = action.payload;
      const cells = { ...state.cells };
      for (const [x, y] of p.cats) {
        const key = cellKey(x, y);
        if (!cells[key]) cells[key] = { kind: "cat", seat: null };
      }
      return {
        ...state,
        cells,
        seats: withScores(state, p.scores),
        turnDeadline: null,
        version: p.version,
        status: "FINISHED",
        result: { reason: p.reason, winner: p.winner },
      };
    }
  }
}
```

`web/src/game/cellSize.ts`:

```ts
export const BOARD_SIZE = 12;
const SIDE_GUTTER_PX = 24;
const MAX_CELL_PX = 40;

/** 화면 폭에 맞는 칸 크기(px). 폭 360px 폰에서 28px, 넓은 화면에서는 40px 로 제한한다. */
export function computeCellSize(viewportWidth: number): number {
  return Math.floor(Math.min((viewportWidth - SIDE_GUTTER_PX) / BOARD_SIZE, MAX_CELL_PX));
}
```

`web/src/api/http.ts`:

```ts
export class ApiError extends Error {
  constructor(
    readonly code: string,
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "DELETE";
  body?: unknown;
  token?: string | null;
}

/** 서버 오류 응답 {code, message} 를 ApiError 로 바꿔 던진다. */
export async function api<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = {};
  if (options.body !== undefined) headers["Content-Type"] = "application/json";
  if (options.token) headers["Authorization"] = `Bearer ${options.token}`;

  const response = await fetch(path, {
    method: options.method ?? "GET",
    headers,
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(data?.code ?? "INTERNAL", data?.message ?? response.statusText, response.status);
  }
  return data as T;
}
```

`web/src/session/sessionStore.ts`:

```ts
import { create } from "zustand";
import { persist } from "zustand/middleware";
import { api, ApiError } from "../api/http";

export interface Player {
  id: string;
  kind: "MEMBER" | "GUEST";
  nickname: string;
  skin1p: number;
  skin2p: number;
}

interface SessionState {
  token: string | null;
  player: Player | null;
  setSession: (token: string, player: Player) => void;
  clear: () => void;
}

export const useSession = create<SessionState>()(
  persist(
    (set) => ({
      token: null,
      player: null,
      setSession: (token, player) => set({ token, player }),
      clear: () => set({ token: null, player: null }),
    }),
    { name: "wheresmeow-session" },
  ),
);

export async function createGuest(nickname: string): Promise<void> {
  const result = await api<{ token: string; player: Player }>("/api/guests", {
    method: "POST",
    body: { nickname },
  });
  useSession.getState().setSession(result.token, result.player);
}

/** 저장된 토큰이 아직 유효한지 확인한다. 서버가 거부하면(재시작 등) 세션을 지운다. */
export async function verifySession(): Promise<void> {
  const { token, clear } = useSession.getState();
  if (!token) return;
  try {
    await api<Player>("/api/players/me", { token });
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) clear();
    else throw error;
  }
}
```

- [ ] **Step 6: 테스트 통과 확인**

Run: `cd web && npx vitest run`
Expected: PASS (Test Files 3 passed, Tests 12 passed)

- [ ] **Step 7: 커밋**

```bash
git add web
git commit -m "feat: 웹 골격과 대국 리듀서·세션 저장소 추가"
```

---

### Task 11: 웹 화면(로비, 초대 입장, 대국)

**Files:**
- Create: `web/src/game/gameStore.ts`
- Create: `web/src/socket/socket.ts`
- Create: `web/src/errorMessages.ts`
- Create: `web/src/game/hooks.ts`
- Create: `web/src/components/Board.tsx`
- Create: `web/src/components/NicknameForm.tsx`
- Create: `web/src/pages/LobbyPage.tsx`, `web/src/pages/JoinRoomPage.tsx`, `web/src/pages/PlayPage.tsx`
- Create: `web/src/App.tsx`, `web/src/main.tsx`, `web/src/styles.css`
- Test: `web/src/components/Board.test.tsx`

**Interfaces:**
- Consumes: Task 10의 모든 공개 이름; 서버 소켓 이벤트 (Task 9)
- Produces: `useGameStore`(game·lastError·dispatch·setError), `bindGameEvents(socket)`; `getSocket(token) -> Socket`; `errorMessage(code)`; `useNavigateOnGameStart()`, `useSecondsLeft(deadline)`, `useViewportWidth()`; `Board({cells, cellSize, disabled, pendingKey, onReveal})`; 라우트 `/`, `/r/:code`, `/play/:gameId`.

- [ ] **Step 1: 실패하는 테스트 작성**

`web/src/components/Board.test.tsx`:

```tsx
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { Board } from "./Board";

afterEach(cleanup);

describe("Board", () => {
  it("[성공] 12x12 칸을 그린다", () => {
    render(<Board cells={{}} cellSize={28} disabled={false} pendingKey={null} onReveal={() => {}} />);

    expect(screen.getAllByRole("button")).toHaveLength(144);
  });

  it("[성공] 닫힌 칸을 누르면 좌표를 넘긴다", () => {
    const onReveal = vi.fn();
    render(<Board cells={{}} cellSize={28} disabled={false} pendingKey={null} onReveal={onReveal} />);

    fireEvent.click(screen.getByLabelText("3,5"));

    expect(onReveal).toHaveBeenCalledWith(3, 5);
  });

  it("[성공] 숫자 칸은 숫자를, 빈 칸은 아무것도 보여 주지 않는다", () => {
    render(
      <Board
        cells={{ "0,0": { kind: "number", n: 2 }, "1,0": { kind: "number", n: 0 } }}
        cellSize={28}
        disabled={false}
        pendingKey={null}
        onReveal={() => {}}
      />,
    );

    expect(screen.getByLabelText("0,0").textContent).toBe("2");
    expect(screen.getByLabelText("1,0").textContent).toBe("");
  });

  it("[실패] 내 차례가 아니면 눌러도 아무 일도 없다", () => {
    const onReveal = vi.fn();
    render(<Board cells={{}} cellSize={28} disabled={true} pendingKey={null} onReveal={onReveal} />);

    fireEvent.click(screen.getByLabelText("0,0"));

    expect(onReveal).not.toHaveBeenCalled();
  });

  it("[실패] 서버 응답을 기다리는 동안에는 다른 칸을 누를 수 없다", () => {
    const onReveal = vi.fn();
    render(<Board cells={{}} cellSize={28} disabled={false} pendingKey="0,0" onReveal={onReveal} />);

    fireEvent.click(screen.getByLabelText("1,1"));

    expect(onReveal).not.toHaveBeenCalled();
  });
});
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `cd web && npx vitest run src/components`
Expected: FAIL — `Failed to resolve import "./Board"`

- [ ] **Step 3: 상태 저장소, 소켓, 오류 문구 작성**

`web/src/game/gameStore.ts`:

```ts
import type { Socket } from "socket.io-client";
import { create } from "zustand";
import { gameReducer } from "./gameReducer";
import type { EndedPayload, GameAction, GameState, RevealedPayload, StartedPayload, TimeoutPayload } from "./types";

interface GameStore {
  game: GameState | null;
  lastError: string | null; // 서버 error 이벤트의 code
  dispatch: (action: GameAction) => void;
  setError: (code: string | null) => void;
}

export const useGameStore = create<GameStore>((set) => ({
  game: null,
  lastError: null,
  dispatch: (action) => set((state) => ({ game: gameReducer(state.game, action) })),
  setError: (code) => set({ lastError: code }),
}));

export function bindGameEvents(socket: Socket): void {
  const { dispatch, setError } = useGameStore.getState();
  socket.on("game:started", (payload: StartedPayload) => {
    setError(null);
    dispatch({ type: "started", payload });
  });
  socket.on("game:revealed", (payload: RevealedPayload) => dispatch({ type: "revealed", payload }));
  socket.on("game:timeout", (payload: TimeoutPayload) => dispatch({ type: "timeout", payload }));
  socket.on("game:ended", (payload: EndedPayload) => dispatch({ type: "ended", payload }));
  socket.on("error", (payload: { code: string }) => setError(payload.code));
}
```

`web/src/socket/socket.ts`:

```ts
import { io, type Socket } from "socket.io-client";
import { bindGameEvents, useGameStore } from "../game/gameStore";
import { useSession } from "../session/sessionStore";

let socket: Socket | null = null;
let socketToken: string | null = null;

/** 토큰마다 연결 하나를 유지한다. 토큰이 바뀌면 이전 연결을 끊고 새로 연다. */
export function getSocket(token: string): Socket {
  if (socket && socketToken === token) return socket;
  socket?.disconnect();
  socket = io({ auth: { token } });
  socketToken = token;
  bindGameEvents(socket);
  socket.on("connect_error", (error) => {
    // 서버가 토큰을 거부하면(서버 재시작 등) 세션을 지우고 닉네임을 다시 받는다
    if (error.message === "UNAUTHORIZED") {
      useGameStore.getState().setError("UNAUTHORIZED");
      useSession.getState().clear();
      socket?.disconnect();
      socket = null;
      socketToken = null;
    }
  });
  return socket;
}
```

`web/src/errorMessages.ts`:

```ts
const MESSAGES: Record<string, string> = {
  ROOM_NOT_FOUND: "방을 찾을 수 없습니다.",
  ROOM_FULL: "이미 대국이 시작된 방입니다.",
  ROOM_EXPIRED: "만료되었거나 취소된 방입니다.",
  NOT_YOUR_TURN: "상대 차례입니다.",
  CELL_ALREADY_OPEN: "이미 열린 칸입니다.",
  ALREADY_IN_GAME: "이미 진행 중인 대국이 있습니다.",
  GAME_FINISHED: "이미 끝난 대국입니다.",
  UNAUTHORIZED: "입장 정보가 만료되었습니다. 닉네임을 다시 입력해 주세요.",
  INVALID_INPUT: "입력값을 확인해 주세요.",
};

export function errorMessage(code: string): string {
  return MESSAGES[code] ?? "오류가 발생했습니다. 잠시 후 다시 시도해 주세요.";
}
```

`web/src/game/hooks.ts`:

```ts
import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { useGameStore } from "./gameStore";

/** 진행 중인 대국이 생기면 대국 화면으로 이동한다. 끝난 대국은 무시한다. */
export function useNavigateOnGameStart(): void {
  const navigate = useNavigate();
  const gameId = useGameStore((s) => (s.game?.status === "IN_PROGRESS" ? s.game.gameId : null));
  useEffect(() => {
    if (gameId) navigate(`/play/${gameId}`);
  }, [gameId, navigate]);
}

/** 마감 시각까지 남은 초(올림). 마감이 없으면 null. */
export function useSecondsLeft(deadline: number | null): number | null {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (deadline === null) return;
    const id = setInterval(() => setNow(Date.now()), 250);
    return () => clearInterval(id);
  }, [deadline]);
  return deadline === null ? null : Math.max(0, Math.ceil((deadline - now) / 1000));
}

export function useViewportWidth(): number {
  const [width, setWidth] = useState(() => window.innerWidth);
  useEffect(() => {
    const onResize = () => setWidth(window.innerWidth);
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);
  return width;
}
```

- [ ] **Step 4: 컴포넌트 작성**

`Board`의 칸 표현(이모지, 단색)은 1단계 임시 표현이다. 3단계에서 시안의 고양이 스킨·들풀·발자국 SVG로 바꾼다.

`web/src/components/Board.tsx`:

```tsx
import { BOARD_SIZE } from "../game/cellSize";
import { cellKey, type Cell } from "../game/types";

interface BoardProps {
  cells: Record<string, Cell>;
  cellSize: number;
  disabled: boolean; // 내 차례가 아니거나 대국이 끝났다
  pendingKey: string | null; // 서버 응답을 기다리는 칸
  onReveal: (x: number, y: number) => void;
}

// 1단계의 임시 표현. 3단계에서 고양이 스킨·들풀·발자국 SVG 로 바꾼다.
function label(cell: Cell | undefined): string {
  if (!cell) return "";
  if (cell.kind === "cat") return "🐱";
  return cell.n > 0 ? String(cell.n) : "";
}

function className(cell: Cell | undefined, pending: boolean): string {
  if (!cell) return pending ? "cell closed pending" : "cell closed";
  if (cell.kind === "number") return "cell open";
  return cell.seat === null ? "cell cat unfound" : `cell cat seat-${cell.seat}`;
}

export function Board({ cells, cellSize, disabled, pendingKey, onReveal }: BoardProps) {
  const buttons = [];
  for (let y = 0; y < BOARD_SIZE; y++) {
    for (let x = 0; x < BOARD_SIZE; x++) {
      const key = cellKey(x, y);
      const cell = cells[key];
      buttons.push(
        <button
          key={key}
          type="button"
          aria-label={`${x},${y}`}
          className={className(cell, key === pendingKey)}
          style={{ width: cellSize, height: cellSize, fontSize: cellSize * 0.5 }}
          disabled={disabled || cell !== undefined || pendingKey !== null}
          onClick={() => onReveal(x, y)}
        >
          {label(cell)}
        </button>,
      );
    }
  }
  return (
    <div className="board" style={{ gridTemplateColumns: `repeat(${BOARD_SIZE}, ${cellSize}px)` }}>
      {buttons}
    </div>
  );
}
```

`web/src/components/NicknameForm.tsx`:

```tsx
import { useState, type FormEvent } from "react";
import { ApiError } from "../api/http";
import { errorMessage } from "../errorMessages";
import { createGuest } from "../session/sessionStore";

export function NicknameForm() {
  const [nickname, setNickname] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await createGuest(nickname);
    } catch (e) {
      setError(e instanceof ApiError ? errorMessage(e.code) : errorMessage("INTERNAL"));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="stack" onSubmit={submit}>
      <label htmlFor="nickname">닉네임 (2~12자)</label>
      <input
        id="nickname"
        value={nickname}
        maxLength={12}
        autoComplete="off"
        onChange={(e) => setNickname(e.target.value)}
      />
      <button className="primary" type="submit" disabled={submitting}>
        게스트로 시작
      </button>
      {error && <p className="error">{error}</p>}
    </form>
  );
}
```

- [ ] **Step 5: 화면과 앱 진입점 작성**

`web/src/pages/LobbyPage.tsx`:

```tsx
import { useState } from "react";
import { api, ApiError } from "../api/http";
import { NicknameForm } from "../components/NicknameForm";
import { errorMessage } from "../errorMessages";
import { useGameStore } from "../game/gameStore";
import { useNavigateOnGameStart } from "../game/hooks";
import { useSession } from "../session/sessionStore";
import { getSocket } from "../socket/socket";

interface RoomResponse {
  code: string;
  status: string;
  expiresAt: number;
}

export function LobbyPage() {
  const { token, player } = useSession();
  const lastError = useGameStore((s) => s.lastError);
  const [room, setRoom] = useState<RoomResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  useNavigateOnGameStart();

  if (!token || !player) {
    return (
      <main className="page">
        <h1 className="logo">Where's Meow</h1>
        <p className="muted">풀숲에 숨은 고양이를 먼저 찾아라</p>
        <NicknameForm />
      </main>
    );
  }

  const inviteLink = room ? `${window.location.origin}/r/${room.code}` : "";

  async function createRoom() {
    setError(null);
    try {
      const created = await api<RoomResponse>("/api/rooms", { method: "POST", token });
      getSocket(token!).emit("room:join", { code: created.code });
      setRoom(created);
    } catch (e) {
      setError(errorMessage(e instanceof ApiError ? e.code : "INTERNAL"));
    }
  }

  function cancelRoom() {
    if (room) getSocket(token!).emit("room:cancel", { code: room.code });
    setRoom(null);
  }

  async function copyLink() {
    await navigator.clipboard.writeText(inviteLink);
    setCopied(true);
  }

  if (room) {
    return (
      <main className="page center">
        <h2>친구를 기다리는 중</h2>
        <div className="room-code">{room.code}</div>
        <button className="primary" type="button" onClick={copyLink}>
          {copied ? "링크를 복사했습니다" : "초대 링크 복사"}
        </button>
        <p className="muted small">{inviteLink}</p>
        <button className="secondary" type="button" onClick={cancelRoom}>
          취소
        </button>
      </main>
    );
  }

  return (
    <main className="page">
      <h1 className="logo">Where's Meow</h1>
      <p className="muted">{player.nickname} (게스트)</p>
      <button className="primary" type="button" onClick={createRoom}>
        친구와 대결
      </button>
      {(error || lastError) && <p className="error">{error ?? errorMessage(lastError!)}</p>}
    </main>
  );
}
```

`web/src/pages/JoinRoomPage.tsx`:

```tsx
import { useEffect, useRef } from "react";
import { Link, useParams } from "react-router";
import { NicknameForm } from "../components/NicknameForm";
import { errorMessage } from "../errorMessages";
import { useGameStore } from "../game/gameStore";
import { useNavigateOnGameStart } from "../game/hooks";
import { useSession } from "../session/sessionStore";
import { getSocket } from "../socket/socket";

export function JoinRoomPage() {
  const { code = "" } = useParams();
  const token = useSession((s) => s.token);
  const lastError = useGameStore((s) => s.lastError);
  const joinedFor = useRef<string | null>(null);
  useNavigateOnGameStart();

  useEffect(() => {
    if (!token || joinedFor.current === token) return;
    joinedFor.current = token;
    useGameStore.getState().setError(null);
    getSocket(token).emit("room:join", { code });
  }, [token, code]);

  return (
    <main className="page center">
      <h2>초대받은 방 {code.toUpperCase()}</h2>
      {!token ? (
        <NicknameForm />
      ) : lastError ? (
        <>
          <p className="error">{errorMessage(lastError)}</p>
          <Link to="/">로비로</Link>
        </>
      ) : (
        <p className="muted">입장하는 중…</p>
      )}
    </main>
  );
}
```

`web/src/pages/PlayPage.tsx`:

```tsx
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router";
import { Board } from "../components/Board";
import { errorMessage } from "../errorMessages";
import { computeCellSize } from "../game/cellSize";
import { useGameStore } from "../game/gameStore";
import { useSecondsLeft, useViewportWidth } from "../game/hooks";
import { cellKey, type GameState } from "../game/types";
import { useSession } from "../session/sessionStore";
import { getSocket } from "../socket/socket";

const REASON_TEXT: Record<NonNullable<GameState["result"]>["reason"], string> = {
  ALL_FOUND: "고양이 25마리를 모두 찾았습니다",
  FORFEIT: "기권으로 끝났습니다",
  AUTO_FORFEIT: "시간 초과 3회 연속으로 자동 기권되었습니다",
};

export function PlayPage() {
  const { gameId } = useParams();
  const token = useSession((s) => s.token);
  const game = useGameStore((s) => s.game);
  const lastError = useGameStore((s) => s.lastError);
  const [pendingKey, setPendingKey] = useState<string | null>(null);
  const [confirmForfeit, setConfirmForfeit] = useState(false);
  const secondsLeft = useSecondsLeft(game?.turnDeadline ?? null);
  const cellSize = computeCellSize(useViewportWidth());

  // 새 이벤트가 오거나 오류가 오면 대기 중 표시를 푼다
  useEffect(() => setPendingKey(null), [game?.version, lastError]);

  if (!token || !game || game.gameId !== gameId) {
    return (
      <main className="page center">
        <p>대국 정보를 불러올 수 없습니다.</p>
        <Link to="/">로비로</Link>
      </main>
    );
  }

  const socket = getSocket(token);
  const me = game.mySeat;
  const opponent = (1 - me) as 0 | 1;
  const myTurn = game.status === "IN_PROGRESS" && game.currentSeat === me;

  function reveal(x: number, y: number) {
    useGameStore.getState().setError(null);
    setPendingKey(cellKey(x, y));
    socket.emit("game:reveal", { gameId: game!.gameId, x, y });
  }

  function forfeit() {
    socket.emit("game:forfeit", { gameId: game!.gameId });
    setConfirmForfeit(false);
  }

  return (
    <main className="play">
      <header className="scoreboard">
        <div className="seat seat-0-text">
          <b>{game.seats[me].nickname}</b>
          <small>나</small>
          <span className="score">{game.seats[me].score}</span>
        </div>
        <span className="vs">VS</span>
        <div className="seat seat-1-text right">
          <span className="score">{game.seats[opponent].score}</span>
          <b>{game.seats[opponent].nickname}</b>
          <small>상대</small>
        </div>
      </header>

      {game.status === "IN_PROGRESS" && (
        <div className="turn">
          <span>{myTurn ? "🐾 내 차례" : "상대 차례"}</span>
          <span>{secondsLeft ?? ""}초</span>
          <div className="timer-bar">
            <i style={{ width: `${((secondsLeft ?? 0) / 20) * 100}%` }} />
          </div>
        </div>
      )}

      <Board
        cells={game.cells}
        cellSize={cellSize}
        disabled={!myTurn}
        pendingKey={pendingKey}
        onReveal={reveal}
      />

      {lastError && <p className="error">{errorMessage(lastError)}</p>}
      {game.outOfSync && <p className="error">화면이 서버와 어긋났습니다. 대국이 끝나면 로비로 돌아가 주세요.</p>}

      <footer className="play-footer">
        <span>
          숨은 고양이 <b>{25 - Object.values(game.cells).filter((c) => c.kind === "cat" && c.seat !== null).length}</b>마리
        </span>
        {game.status === "IN_PROGRESS" &&
          (confirmForfeit ? (
            <span>
              <button className="danger" type="button" onClick={forfeit}>
                기권 확정
              </button>
              <button className="ghost" type="button" onClick={() => setConfirmForfeit(false)}>
                계속하기
              </button>
            </span>
          ) : (
            <button className="ghost" type="button" onClick={() => setConfirmForfeit(true)}>
              기권
            </button>
          ))}
      </footer>

      {game.result && (
        <section className="result">
          <h2>
            {game.result.winner === null ? "무승부" : game.result.winner === me ? "승리!" : "패배"}
          </h2>
          <p className="big">
            {game.seats[me].score} : {game.seats[opponent].score}
          </p>
          <p className="muted">{REASON_TEXT[game.result.reason]}</p>
          <Link className="primary" to="/">
            로비로
          </Link>
        </section>
      )}
    </main>
  );
}
```

`web/src/App.tsx`:

```tsx
import { useEffect } from "react";
import { BrowserRouter, Route, Routes } from "react-router";
import { JoinRoomPage } from "./pages/JoinRoomPage";
import { LobbyPage } from "./pages/LobbyPage";
import { PlayPage } from "./pages/PlayPage";
import { verifySession } from "./session/sessionStore";

export function App() {
  useEffect(() => {
    verifySession().catch((error) => console.error("세션 확인 실패", error));
  }, []);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LobbyPage />} />
        <Route path="/r/:code" element={<JoinRoomPage />} />
        <Route path="/play/:gameId" element={<PlayPage />} />
      </Routes>
    </BrowserRouter>
  );
}
```

`web/src/main.tsx`:

```tsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import "./styles.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
```

`web/src/styles.css`:

```css
/* 1단계 임시 스타일. 3단계에서 시안(들풀·발자국·스킨)으로 교체한다. */
:root {
  --bg: #eef6e4;
  --ink: #2f3a24;
  --grass: #5c9a35;
  --grass-dark: #3f6b28;
  --dirt: #e9d8b4;
  --seat-0: #e07b2a;
  --seat-1: #36323c;
  --danger: #c92a2a;
  font-family: system-ui, -apple-system, sans-serif;
  color: var(--ink);
  background: var(--bg);
}

* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); }
button { font: inherit; touch-action: manipulation; }

.page { max-width: 420px; margin: 0 auto; padding: 32px 16px; display: flex; flex-direction: column; gap: 12px; }
.page.center { align-items: center; text-align: center; }
.stack { display: flex; flex-direction: column; gap: 8px; }
.logo { margin: 0; color: var(--grass-dark); }
.muted { opacity: 0.65; }
.small { font-size: 12px; word-break: break-all; }
.error { color: var(--danger); }
input { font: inherit; padding: 10px 12px; border-radius: 10px; border: 1.5px solid #b9d3a3; }
.primary, .secondary, .danger, .ghost { border-radius: 12px; padding: 12px 16px; font-weight: 700; border: 0; text-decoration: none; text-align: center; }
.primary { background: var(--grass); color: #fff; }
.secondary { background: #fff; color: var(--grass-dark); border: 1.5px solid #b9d3a3; }
.danger { background: var(--danger); color: #fff; padding: 6px 12px; }
.ghost { background: transparent; border: 1.5px solid #9bb08a; padding: 6px 12px; }
.room-code { font-size: 32px; font-weight: 800; letter-spacing: 4px; background: #fff; padding: 8px 16px; border-radius: 12px; }

.play { max-width: 520px; margin: 0 auto; padding: 8px 12px 24px; display: flex; flex-direction: column; align-items: center; gap: 8px; }
.scoreboard { width: 100%; display: flex; justify-content: space-between; align-items: center; background: #fff; border-radius: 12px; padding: 8px 12px; }
.seat { display: flex; align-items: center; gap: 6px; }
.seat small { opacity: 0.6; }
.score { font-size: 24px; font-weight: 800; }
.seat-0-text .score { color: var(--seat-0); }
.seat-1-text .score { color: var(--seat-1); }
.vs { opacity: 0.35; font-weight: 800; font-size: 12px; }
.turn { width: 100%; display: flex; justify-content: space-between; flex-wrap: wrap; font-weight: 700; }
.timer-bar { width: 100%; height: 6px; background: #d5e3c7; border-radius: 3px; }
.timer-bar i { display: block; height: 100%; background: var(--seat-0); border-radius: 3px; transition: width 0.25s linear; }

.board { display: grid; gap: 1px; padding: 4px; background: var(--grass-dark); border-radius: 8px; }
.cell { padding: 0; border: 0; border-radius: 3px; display: flex; align-items: center; justify-content: center; font-weight: 800; color: var(--ink); }
.cell.closed { background: var(--grass); }
.cell.closed:enabled { cursor: pointer; }
.cell.pending { background: #86c94f; }
.cell.open, .cell.cat { background: var(--dirt); }
.cell.cat.seat-0 { box-shadow: inset 0 0 0 2px var(--seat-0); }
.cell.cat.seat-1 { box-shadow: inset 0 0 0 2px var(--seat-1); }
.cell.cat.unfound { opacity: 0.45; }

.play-footer { width: 100%; display: flex; justify-content: space-between; align-items: center; gap: 8px; }
.result { position: fixed; inset: 0; background: rgba(238, 246, 228, 0.94); display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px; }
.result h2 { font-size: 40px; margin: 0; color: var(--seat-0); }
.big { font-size: 32px; font-weight: 800; margin: 0; }
```

- [ ] **Step 6: 테스트·타입 검사·빌드 확인**

Run: `cd web && npx vitest run`
Expected: PASS (Test Files 4 passed, Tests 17 passed)

Run: `cd web && npm run build`
Expected: `tsc --noEmit` 오류 없음, `✓ built in ...`

- [ ] **Step 7: 커밋**

```bash
git add web
git commit -m "feat: 로비·초대 입장·대국 화면 추가"
```

---

### Task 12: 전체 흐름 확인

**Files:**
- Create: `web/scripts/smoke.mjs`

**Interfaces:**
- Consumes: 개발 서버(5000)와 Vite 개발 서버(5173, 프록시 포함)

- [ ] **Step 1: 자동 확인 스크립트 작성**

Vite 프록시를 거쳐 게스트 두 명이 초대 방으로 대국을 시작하고, 한 수를 두고, 기권으로 끝내는 흐름을 확인한다.

`web/scripts/smoke.mjs`:

```js
// Vite 프록시(5173)를 거쳐 게스트 두 명이 초대 방으로 대국을 시작하고 한 수 두는지 확인한다.
import { io } from "socket.io-client";

const BASE = "http://127.0.0.1:5173";
const post = async (path, body, token) => {
  const res = await fetch(BASE + path, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    body: body ? JSON.stringify(body) : undefined,
  });
  return res.json();
};
const once = (socket, name) => new Promise((resolve) => socket.once(name, resolve));

const a = await post("/api/guests", { nickname: "방장냥" });
const b = await post("/api/guests", { nickname: "손님냥" });
const room = await post("/api/rooms", null, a.token);
const sa = io(BASE, { auth: { token: a.token } });
const sb = io(BASE, { auth: { token: b.token } });
await Promise.all([once(sa, "connect"), once(sb, "connect")]);

const waiting = once(sa, "room:waiting");
sa.emit("room:join", { code: room.code });
console.log("waiting:", (await waiting).code === room.code);

const startedA = once(sa, "game:started");
const startedB = once(sb, "game:started");
sb.emit("room:join", { code: room.code });
const [ga, gb] = await Promise.all([startedA, startedB]);
console.log("started:", ga.gameId === gb.gameId, "seats:", ga.mySeat, gb.mySeat, "first:", ga.currentSeat);

const mover = ga.currentSeat === ga.mySeat ? sa : sb;
const revealed = once(sa, "game:revealed");
mover.emit("game:reveal", { gameId: ga.gameId, x: 5, y: 5 });
const r = await revealed;
console.log("revealed version:", r.version, "cells:", r.cells.length);

const ended = once(sb, "game:ended");
sa.emit("game:forfeit", { gameId: ga.gameId });
const e = await ended;
console.log("ended:", e.reason, "winner:", e.winner, "cats:", e.cats.length);
sa.close();
sb.close();
```

- [ ] **Step 2: 서버 두 개를 띄우고 스크립트 실행**

터미널 1: `cd server && .venv/bin/python -m wheresmeow`
터미널 2: `cd web && npx vite --host 127.0.0.1 --port 5173 --strictPort`
터미널 3: `cd web && node scripts/smoke.mjs`

Expected:

```
waiting: true
started: true seats: 0 1 first: 0 또는 1
revealed version: 1 cells: 1 이상
ended: FORFEIT winner: 0 또는 1 cats: 25
```

- [ ] **Step 3: 브라우저 두 개로 직접 확인**

일반 창과 시크릿 창(서로 다른 localStorage)으로 `http://127.0.0.1:5173`을 연다. 모바일 화면 확인은 개발자 도구의 기기 모드(폭 360px)를 쓴다.

1. 창 A: 닉네임 입력 → "친구와 대결" → 방 코드와 초대 링크가 보인다.
2. 창 B: 초대 링크를 연다 → 닉네임 입력 → 두 창 모두 대국 화면으로 이동한다.
3. 차례인 창에서 칸을 누른다 → 두 창에 같은 결과가 보이고, 숫자 칸이면 차례가 넘어간다.
4. 아무것도 누르지 않고 20초를 기다린다 → 차례인 쪽 점수가 -1 되고 차례가 넘어간다.
5. 차례가 아닌 창에서 칸을 누를 수 없다(버튼 비활성).
6. 한쪽에서 "기권" → "기권 확정" → 두 창에 결과 화면이 뜨고, 아무도 못 찾은 고양이가 흐리게 공개된다.
7. 폭 360px에서 판이 가로 스크롤 없이 화면 안에 들어간다.

`ui-test` 스킬로 이 목록을 AI 테스터에게 맡길 수도 있다.

- [ ] **Step 4: 전체 테스트 재실행**

Run: `cd server && .venv/bin/pytest`
Expected: PASS (109 passed)

Run: `cd web && npx vitest run`
Expected: PASS (17 passed)

- [ ] **Step 5: 커밋**

```bash
git add web/scripts/smoke.mjs
git commit -m "test: 초대 대국 전체 흐름 자동 확인 스크립트 추가"
```
