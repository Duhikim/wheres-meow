# Where's Meow 설계 스펙

- 작성일: 2026-10-12
- 상태: 사용자 검토 대기
- 시안: [`2026-10-12-wheres-meow-mockups/`](2026-10-12-wheres-meow-mockups/) (스킨·잔디, 모바일 화면 배치와 흐름)

## 1. 개요

**Where's Meow**는 모바일 브라우저에서도 플레이할 수 있는 웹 기반 1:1 대전 게임이다. 지뢰찾기 규칙을 바탕으로 한다. 두 사람이 하나의 판을 번갈아 열면서 풀숲에 숨은 고양이(지뢰)를 더 많이 찾는 쪽이 이긴다(Minesweeper Flags 방식). 불특정 다수가 접속하는 **공개 서비스**로 운영한다.

### 1.1 성공 기준

1. 폭 360px 세로 화면에서 확대 없이 한 판을 끝까지 둘 수 있다.
2. 초대 링크 하나로 두 사람이 가입 없이(게스트) 바로 대국을 시작할 수 있다.
3. 랜덤 매칭으로 비슷한 레이팅의 상대와 짝지어지고, 대국 결과가 레이팅과 랭킹에 반영된다.
4. 컴퓨터와 세 가지 난이도로 대국할 수 있고, 그 전적은 사람 간 전적과 따로 보인다.
5. 대국 중 연결이 끊겨도 다시 연결되면 화면이 그대로 복원된다.
6. 클라이언트는 어떤 경우에도 닫힌 칸의 정답(고양이 위치)을 대국이 끝나기 전에 받지 않는다.

### 1.2 사용자가 결정한 사항

| 항목 | 결정 |
|---|---|
| 서비스 이름 | Where's Meow (영문으로 통일, 한국어 이름 없음). 코드 패키지 `wheresmeow`, 환경 변수 접두사 `WHERESMEOW_`. 저장소 폴더명 `mind-finder`는 유지 |
| 목적 | 공개 서비스 운영 |
| 대결 방식 | 공유 판 턴제, 지뢰를 찾으면 득점하고 한 번 더 둠 |
| 판 | 12×12, 고양이 25마리 |
| 종료 조건 | 25마리를 모두 찾거나 기권. 13점 도달로 조기 종료하지 않음 |
| 턴 시간 | 20초. 초과하면 -1점, 턴 넘김. 3회 연속 초과하면 자동 기권 |
| 동점 | 무승부 (Elo 0.5) |
| 음수 점수 | 허용 |
| 첫 출시 범위 | 초대 링크·방 코드, 회원 계정, 랜덤 매칭, 레이팅·랭킹, 재대결, 컴퓨터 대전 |
| 대국 모드 | 랭크·일반 구분 없음. 사람끼리의 모든 대국이 레이팅에 반영됨 |
| 게스트 | 모든 기능 사용 가능. 임시 레이팅을 가지며 랭킹에는 나오지 않음 |
| 로그인 수단 | 자체 가입(아이디·비밀번호·닉네임), Google, Naver, Kakao |
| 컴퓨터 대전 | 난이도 3단계, 전적은 별도 관리(게스트 포함 서버 저장), 레이팅 미반영 |
| 스택 | Python, Flask, Flask-SocketIO, React |
| 접근 방식 | 단일 서버 + PostgreSQL. 진행 중 상태는 메모리, 포트 뒤에 숨김 |
| 아키텍처 | 헥사고널. 도메인별 패키지를 먼저 나누고, REST·소켓 모두 도메인별 inbound 어댑터에 둠 |
| 테마 | 지뢰는 고양이, 열린 칸은 고양이 발자국 위에 숫자, 닫힌 칸은 키 큰 들풀 |
| 스킨 | 10종 중 1P·2P를 고름. 기본 16번(1P), 17번(2P). 겹치면 우선권 없는 쪽이 2P |
| 스킨 우선권 | 초대 방은 방장, 랜덤 매칭은 대기열 선착순 |
| 대국 화면 | A안(상단 점수판) |

### 1.3 설계 중 내린 가정

- 서비스 언어는 한국어 하나다.
- 진행 중인 대국은 서버 재시작 시 사라지는 것을 허용한다(배포는 대국이 적은 시간에 한다).
- 서버 프로세스는 하나다. 수평 확장이 필요해지면 `GameStore`·`MatchQueue` 등의 outbound 어댑터를 Redis 구현으로 교체한다.

## 2. 게임 규칙

1. 판은 12×12이고 고양이 25마리를 서버가 `secrets` 기반 난수로 배치한다.
2. 선공은 무작위로 정한다. 재대결은 직전 대국의 후공이 선공이다.
3. 자기 차례에 닫힌 칸 하나를 연다.
   - 고양이면 +1점, **같은 플레이어가 한 번 더** 둔다. 찾은 고양이는 찾은 플레이어의 스킨으로 표시된다.
   - 숫자 칸이면 그 칸만 열고 턴이 넘어간다.
   - 빈 칸(주변 고양이 0)이면 연결된 영역을 연쇄로 열고 턴이 넘어간다. 연쇄 열기는 고양이 칸을 열지 않는다.
4. 20초 안에 두지 않으면 -1점을 받고 턴이 넘어간다. 점수는 음수가 될 수 있다.
5. 정상적으로 두면 그 플레이어의 연속 시간 초과 횟수를 0으로 되돌린다. 연속 3회 시간 초과하면 자동 기권패다.
6. 종료 조건
   - 25마리를 모두 찾음: 점수가 높은 쪽이 승리, 같으면 무승부.
   - 기권 또는 자동 기권: 기권한 쪽이 패배(점수와 무관).
7. 깃발 기능은 없다. 고양이를 찾는 행위 자체가 득점이기 때문이다.
8. 고양이 위치 전체는 대국 종료 이벤트에서만 공개한다.

## 3. 아키텍처

### 3.1 전체 구성

- **서버**: Flask + Flask-SocketIO, gevent 워커 **1개**(`gunicorn -w 1 -k geventwebsocket...`). 진행 중 상태가 메모리에 있으므로 프로세스를 늘리지 않는다.
- **DB**: PostgreSQL. SQLAlchemy 2.0, 마이그레이션은 Alembic. 모델은 SQLAlchemy 범용 타입만 사용한다(통합 테스트에서 SQLite를 쓰기 위함).
- **클라이언트**: React + Vite + TypeScript, react-router, socket.io-client, Zustand.
- **배포 기준선**: Docker 이미지와 docker compose(app, postgres, nginx). nginx는 정적 파일 제공과 WebSocket 프록시를 맡는다. 실제 호스팅 업체는 배포 단계에서 고른다.
- 게임 판정은 전부 서버가 한다(server-authoritative).

### 3.2 헥사고널 패키지 구조

도메인별 패키지를 최상위에 두고, 각 도메인 안을 `domain` → `application`(포트, 서비스) → `adapter`(inbound, outbound)로 나눈다. Python에서 `in`은 예약어이므로 `inbound`·`outbound`라는 이름을 쓴다. 포트는 `typing.Protocol` 또는 `abc.ABC`로 정의한다.

```
server/
├── pyproject.toml
├── src/wheresmeow/
│   ├── game/
│   │   ├── domain/                 Board, Cell, Game, Score, 도메인 예외 (순수 Python)
│   │   ├── application/
│   │   │   ├── port/inbound/       StartGame, RevealCell, Forfeit, GetGame, SyncGame, RequestRematch 유스케이스
│   │   │   ├── port/outbound/      GameStore, GameEventPublisher, TurnTimer, GameResultRecorder, Clock
│   │   │   └── service/            GameService, RematchService
│   │   └── adapter/
│   │       ├── inbound/socket/     game:* 이벤트 핸들러
│   │       ├── inbound/web/        GET /api/games/*
│   │       ├── outbound/memory/    InMemoryGameStore
│   │       ├── outbound/timer/     GeventTurnTimer
│   │       ├── outbound/socket/    SocketIOGameEventPublisher
│   │       └── outbound/result/    결과 기록 어댑터 (rating·bot 도메인 유스케이스 호출)
│   ├── room/                       초대 방 (같은 구조)
│   ├── matchmaking/                단일 대기열 (같은 구조)
│   ├── account/                    players, 자체 가입, OAuth, 게스트, 토큰, 스킨 설정 (같은 구조)
│   ├── rating/                     Elo, 사람 간 전적, 랭킹, 프로필 (같은 구조)
│   ├── bot/                        봇 판단(solver), 봇 차례 진행, 봇 전적 (같은 구조)
│   ├── shared/                     공통 예외 기반 클래스, ID 타입, 오류 코드
│   └── bootstrap/                  Flask 앱 팩토리, 설정, 의존성 조립
└── tests/                          src 구조를 그대로 따름. 각 도메인 아래 integration/ 패키지
web/
└── src/ (pages, components, game, socket, store, skins)
```

### 3.3 의존 규칙

- `domain`은 아무것도 import하지 않는다(표준 라이브러리 제외).
- `application`은 자기 도메인의 `domain`과 포트만 안다.
- `adapter`는 Flask, SQLAlchemy, Socket.IO 등 프레임워크를 아는 유일한 계층이다. ORM 모델은 `adapter/outbound/persistence`에만 있고, 도메인 엔티티와는 매핑 함수로 변환한다.
- 도메인 사이의 호출은 반드시 포트를 거친다. 예: 대국이 끝나면 `game`은 `GameResultRecorder` 포트만 부르고, 그 어댑터가 `rating` 또는 `bot`의 유스케이스를 부른다. `game`은 `rating`과 `bot`의 존재를 모른다.
- 의존성 조립은 `bootstrap/`에서 생성자를 직접 호출해 처리한다. DI 라이브러리는 쓰지 않는다.

## 4. 도메인 설계

### 4.1 game

- **Board**: 크기, 고양이 위치 집합, 칸별 주변 고양이 수. 생성기는 포트(`MineLayoutGenerator`)로 분리해 테스트와 E2E에서 고정 배치를 주입할 수 있게 한다.
- **Game**: `id`, 두 `Seat`(player_id, 닉네임, 스킨, 점수, 연속 시간 초과 횟수, 봇 여부), `current_seat`, 열린 칸(고양이라면 찾은 좌석), `status`(IN_PROGRESS, FINISHED), `end_reason`(ALL_FOUND, FORFEIT, AUTO_FORFEIT), `winner`(좌석 또는 무승부), `version`, `turn_seq`, `turn_deadline`, `mode`(INVITE, MATCH, BOT), 수순 기록.
- **동작**: `reveal(player_id, x, y)`, `timeout(turn_seq)`, `forfeit(player_id)`. 모든 동작은 성공하면 `version`을 1 올리고 이벤트 목록을 돌려준다. 규칙 위반은 도메인 예외를 던진다.
- **동시성**: 대국마다 gevent `Semaphore` 하나. `reveal`·`timeout`·`forfeit`는 이 잠금 안에서 실행하고, 잠금은 컨텍스트 매니저로 감싸 예외가 나도 풀리게 한다.
- **턴 타이머**: 턴이 바뀔 때마다 `turn_seq`를 올리고 `TurnTimer.schedule(game_id, turn_seq, deadline)`을 호출한다. 만료 시 `timeout(turn_seq)`는 전달받은 `turn_seq`가 현재 값과 같을 때만 적용한다. 봇 좌석의 턴에는 타이머를 걸지 않는다.
- **활성 대국 제한**: 한 플레이어는 진행 중인 대국을 하나만 가질 수 있다(`ALREADY_IN_GAME`).
- **스킨 배정**: 대국 생성 시 서버가 정한다. 각자 1P를 쓰고, 1P가 같으면 우선권이 없는 쪽이 2P를 쓴다. 1P와 2P는 항상 다르므로 이 규칙만으로 충돌이 사라진다. 봇 대국에서는 사람이 1P, 봇이 그 사람의 2P를 쓴다.
- **재대결 (`RematchService`)**
  - 종료된 대국에 대해 한쪽이 요청하면 상대에게 알린다. 상대가 수락하거나 양쪽이 모두 요청하면 같은 두 사람, 같은 모드, 같은 스킨 배정, 선공을 바꾼 새 대국을 만든다.
  - 요청은 30초가 지나거나, 상대가 거절하거나, 상대가 결과 화면을 떠나면(`game:leave-result`) 무효다.
  - 봇 대국의 재대결은 봇이 즉시 수락한다.

### 4.2 room

- `POST /api/rooms`로 방을 만든다. 만든 사람이 방장(스킨 우선권)이다.
- 방 코드는 6자리이며 알파벳 `ABCDEFGHJKLMNPQRSTUVWXYZ23456789`(0·O·1·I 제외)에서 뽑는다. 링크는 `/r/{코드}`.
- 두 번째 사람이 `room:join`하면 `game` 도메인의 `StartGame` 유스케이스를 포트로 호출하고 방을 닫는다. 세 번째 사람은 `ROOM_FULL`.
- 방장이 자기 방에 다시 들어오는 요청은 무시한다(멱등).
- 10분 동안 상대가 오지 않으면 만료(`ROOM_EXPIRED`). 방장이 취소할 수도 있다.
- 초대 대국도 레이팅에 반영한다.

### 4.3 matchmaking

- 대기열은 하나다. `match:join`으로 들어가고 `match:leave`로 나온다. 연결이 끊기면 자동으로 빠진다.
- 짝짓기 기준: 레이팅 차이 ±100에서 시작해 5초마다 ±50씩 넓히고, 30초가 지나면 범위 제한 없이 누구와도 짝짓는다.
- 짝짓기는 1초 주기의 백그라운드 작업이 수행한다. 대기열 전체를 하나의 잠금으로 보호해 같은 사람이 두 대국에 배정되지 않게 한다.
- 대기열에 먼저 들어온 사람이 스킨 우선권을 갖는다.
- 게스트도 자신의 임시 레이팅으로 같은 대기열에 들어간다.

### 4.4 account

- **players**: 회원과 게스트 모두의 공통 신원. 닉네임과 스킨 설정을 가진다.
- **자체 가입**: 아이디 4~20자(`[a-z0-9_]`), 비밀번호 8자 이상, 닉네임 2~12자. 회원 닉네임은 서비스 전체에서 유일하다. 비밀번호는 argon2(`argon2-cffi`)로 해시한다. 로그인 시도는 Flask-Limiter로 IP당 분당 10회로 제한한다.
- **OAuth**: Google, Naver, Kakao를 Authlib으로 연동한다. 서버에서 Authorization Code 흐름을 처리한다. 첫 로그인 시 계정을 만들고 닉네임 설정 화면으로 보낸다. 제공자가 다르면 같은 이메일이라도 별도 계정이다.
- **토큰**: 액세스 토큰은 JWT 15분, 클라이언트 메모리에만 보관한다. 리프레시 토큰은 14일, httpOnly·Secure·SameSite 쿠키로 보내고 사용할 때마다 새로 발급한다(rotation). DB에는 해시만 저장하고 로그아웃 시 폐기한다.
- **게스트**: `POST /api/guests {nickname}`으로 players 행과 서명된 게스트 토큰을 만든다. 토큰은 30일이며 사용할 때마다 만료일을 30일 뒤로 연장한다. 게스트 닉네임은 중복을 허용하고 화면에 "게스트" 표시를 붙인다.
- **스킨 설정**: `PUT /api/players/me/skins {skin1p, skin2p}`. 허용 ID는 `9, 10, 11, 12, 16, 17, 18, 19, 20, 21`이며, 허용하지 않는 ID이거나 두 값이 같으면 `INVALID_SKIN`. 회원과 게스트 모두 서버에 저장한다.
- 소켓 연결 시 `auth`에 액세스 토큰 또는 게스트 토큰을 실어 보내고, 검증에 실패하면 연결을 거부한다.

### 4.5 rating

- Elo, 초기 1000, K=32. 승리 1, 무승부 0.5, 패배·기권·자동 기권 0.
- 사람 간 모든 대국(초대, 매칭, 재대결)에 적용한다. 게스트도 레이팅을 가진다.
- 대국 결과 저장, 레이팅 갱신, `rating_changes` 기록을 한 트랜잭션으로 처리한다.
- **랭킹** `GET /api/rankings?page=`: 회원이면서 레이팅 대국 5판 이상인 플레이어만 레이팅 순으로 보여 준다.
- **프로필** `GET /api/players/{id}`: 레이팅, 승·패·무, 최근 대국 20판, 컴퓨터 대전 난이도별 전적.

### 4.6 bot

- **판단(solver, 순수 도메인)**: 입력은 사람에게 보이는 정보뿐이다(열린 칸, 숫자, 찾은 고양이 위치, 남은 고양이 수). 정답 배치를 절대 받지 않는다.
  - **쉬움**: 숫자 하나로 확정되는 고양이 칸이 있으면 30% 확률로 그 칸을 고르고, 나머지는 닫힌 칸 중 무작위로 고른다.
  - **보통**: 숫자 하나로 확정되는 고양이 칸이 있으면 반드시 고른다. 없으면 무작위로 고른다.
  - **어려움**: 여러 숫자를 엮은 제약 추론으로 확정 고양이 칸을 찾는다. 없으면 각 닫힌 칸이 고양이일 확률을 계산해 가장 높은 칸을 고른다. 확률은 경계 칸(열린 숫자에 닿은 닫힌 칸)을 서로 독립인 구간으로 나눈 뒤 구간별로 가능한 배치를 모두 세어 구한다. 한 구간의 경계 칸이 24개를 넘으면 그 구간은 각 숫자의 남은 고양이 수 / 남은 닫힌 칸 수 중 최댓값을 확률로 쓰는 국소 근사로 대체한다.
- **진행**: `game`의 `GameEventPublisher` 포트를 구현한 봇 어댑터가 "봇의 차례가 됨" 이벤트를 받으면 0.8~2초 뒤에 `RevealCell` 유스케이스를 호출한다. 봇은 시간 초과를 하지 않는다.
- **시작**: 소켓 `bot:start {difficulty}`. 난이도는 EASY, NORMAL, HARD.
- **전적**: `bot_records(player_id, difficulty, wins, losses, draws)`. 레이팅과 랭킹에는 반영하지 않는다.

## 5. 인터페이스 계약

### 5.1 REST API

| 메서드·경로 | 설명 |
|---|---|
| `POST /api/guests` | 게스트 생성, 게스트 토큰 발급 |
| `POST /api/auth/signup` | 자체 가입 |
| `POST /api/auth/login` | 자체 로그인 |
| `POST /api/auth/refresh` | 액세스 토큰 재발급(리프레시 토큰 rotation) |
| `POST /api/auth/logout` | 리프레시 토큰 폐기 |
| `GET /api/auth/oauth/{provider}/authorize` | 제공자 로그인 페이지로 리다이렉트 |
| `GET /api/auth/oauth/{provider}/callback` | 콜백 처리 후 클라이언트로 리다이렉트 |
| `GET /api/players/me` | 내 정보(닉네임, 종류, 스킨, 레이팅) |
| `PUT /api/players/me/nickname` | 닉네임 설정·변경 |
| `PUT /api/players/me/skins` | 1P·2P 스킨 설정 |
| `GET /api/players/{id}` | 프로필 |
| `GET /api/rankings` | 랭킹 |
| `POST /api/rooms` | 초대 방 생성 |
| `GET /api/rooms/{code}` | 방 상태 확인(입장 전) |
| `GET /api/games/current` | 내 진행 중 대국 ID(없으면 204) |

오류 응답은 `{"code": "...", "message": "..."}` 형식과 적절한 HTTP 상태 코드를 쓴다.

### 5.2 Socket.IO 이벤트

| 방향 | 이벤트 | 내용 |
|---|---|---|
| C→S | `room:join` | `code` |
| C→S | `room:cancel` | `code` |
| C→S | `match:join` / `match:leave` | 없음 |
| C→S | `bot:start` | `difficulty` |
| C→S | `game:reveal` | `gameId, x, y` |
| C→S | `game:forfeit` | `gameId` |
| C→S | `game:sync` | `gameId` |
| C→S | `game:rematch-request` / `game:rematch-decline` | `gameId` |
| C→S | `game:leave-result` | `gameId` |
| S→C | `room:waiting` | `code, expiresAt` |
| S→C | `match:waiting` | `since, range` |
| S→C | `game:started` | 대국 ID, 두 좌석(닉네임, 스킨, 봇 여부), 내 좌석, 선공, 마감 시각, `version` |
| S→C | `game:state` | 전체 스냅샷(열린 칸, 찾은 고양이와 좌석, 점수, 현재 턴, 마감 시각, 연속 시간 초과 횟수, `version`) |
| S→C | `game:revealed` | 열린 칸 목록, 둔 좌석, 점수, 다음 턴, 마감 시각, `version` |
| S→C | `game:timeout` | 감점 좌석, 점수, 다음 턴, 마감 시각, `version` |
| S→C | `game:ended` | 종료 사유, 승자 또는 무승부, 최종 점수, 고양이 전체 위치, 레이팅 변화(사람 간 대국만, 저장 실패 시 null), `version` |
| S→C | `game:rematch-requested` / `game:rematch-cancelled` | `gameId` (취소 사유 포함) |
| S→C | `error` | `code, message` |

- 모든 대국 이벤트의 `version`은 1씩 증가한다. 클라이언트가 건너뛴 번호를 발견하면 `game:sync`를 보낸다.
- 마감 시각은 서버 기준 epoch ms다. 카운트다운 표시는 클라이언트가 한다.
- 소켓 룸 이름은 `game:{id}`, `room:{code}`, `player:{id}`를 쓴다.

## 6. 데이터 모델

| 테이블 | 주요 컬럼 |
|---|---|
| `players` | id(UUID), kind(MEMBER·GUEST), nickname, skin_1p, skin_2p, created_at, last_seen_at |
| `accounts` | player_id(PK, FK), username(unique, 자체 가입만), password_hash |
| `oauth_identities` | player_id, provider, provider_user_id — (provider, provider_user_id) unique |
| `refresh_tokens` | id, player_id, token_hash, expires_at, revoked_at |
| `ratings` | player_id(PK), rating, games, wins, losses, draws, updated_at |
| `game_records` | id, mode(INVITE·MATCH·BOT), bot_difficulty, 두 좌석의 player_id·닉네임 스냅샷·스킨, 점수, 승자 좌석(무승부면 null), end_reason, 고양이 배치(JSON), 수순 기록(JSON), started_at, ended_at |
| `rating_changes` | game_id, player_id, before, after |
| `bot_records` | player_id, difficulty, wins, losses, draws — (player_id, difficulty) PK |

- 회원 닉네임 유일성은 애플리케이션 서비스에서 먼저 검증하고(`NICKNAME_TAKEN`), DB에도 `players(nickname) WHERE kind='MEMBER'` 부분 유일 인덱스를 둔다. PostgreSQL과 SQLite 모두 부분 인덱스를 지원하므로 SQLAlchemy의 `postgresql_where`·`sqlite_where`로 같은 인덱스를 선언한다.
- 봇 좌석의 player_id는 고정 값 `bot:EASY`, `bot:NORMAL`, `bot:HARD`로 기록하고 `players`를 참조하지 않는다.

## 7. 화면 설계

### 7.1 시각 테마

- 고양이 스킨 10종: 16(치즈 태비), 17(까망이), 18(삼색이), 19(회색 태비), 20(샴), 21(흰둥이), 9(턱시도), 10(러시안블루), 11(고등어), 12(접힌 귀 회색 태비). 모두 풀숲에서 빼꼼 내다보는 자세다.
- 닫힌 칸: 키 큰 들풀. 칸 번호를 시드로 풀 모양을 정해 모든 화면에서 같게 보인다. 일부 칸에는 작은 꽃이 있다.
- 열린 칸: 흙바닥. 숫자 칸은 고양이 발자국의 큰 발바닥 위에 숫자를 쓴다.
- 고양이와 잔디는 시안의 파라미터 방식 SVG를 React 컴포넌트로 옮긴다. 이미지 파일은 쓰지 않는다.
- 찾은 고양이의 스킨이 곧 누가 찾았는지를 나타내므로 별도의 색 표시는 하지 않는다.

### 7.2 라우트

| 경로 | 화면 |
|---|---|
| `/` | 로비: 빠른 대전, 친구와 대결, 컴퓨터와 대결(난이도 선택), 랭킹, 내 고양이, 설정, 로그인 |
| `/r/:code` | 초대 링크 입장. 게스트라면 닉네임 입력 후 입장 |
| `/play/:gameId` | 대국. 종료 후 같은 경로에서 결과 화면 |
| `/ranking`, `/players/:id` | 랭킹, 프로필 |
| `/me/cats` | 내 고양이 설정(1P·2P) |
| `/login`, `/signup`, `/auth/callback/:provider` | 로그인, 자체 가입, 소셜 로그인 콜백 |

초대 대기와 매칭 대기는 로비 위의 전체 화면 상태로 처리한다.

### 7.3 대국 화면 (A안: 상단 점수판)

- 위: 두 사람의 고양이 얼굴, 닉네임, 점수. 그 아래 "내 차례·상대 차례" 표시와 20초 타이머 막대.
- 가운데: 12×12 판. 칸 크기 `min((화면 폭 - 24px) / 12, 40px)`.
- 아래: 남은 고양이 수, 기권 버튼(확인 단계 포함).
- 탭하면 바로 연다. 낙관적 갱신은 하지 않고 서버 응답 전까지 눌린 상태로만 표시한다.
- `touch-action: manipulation`으로 더블탭 확대를 막는다.
- 고양이를 찾으면 풀이 흔들리며 고양이가 튀어나오는 짧은 애니메이션. `prefers-reduced-motion`이면 끈다.
- 연결이 끊기면 "다시 연결하는 중" 배너를 띄운다.

### 7.4 결과 화면

- 승리·패배·무승부, 최종 점수, 종료 사유, 레이팅 변화(사람 간 대국).
- 재대결 신청, 로비로 버튼. 상대의 재대결 요청이 오면 수락·거절 버튼을 보여 준다.

### 7.5 클라이언트 상태

- 대국 상태는 서버 이벤트를 `version` 순서로 적용하는 리듀서 하나로 관리한다.
- 앱 시작 시와 재연결 시 `GET /api/games/current`를 확인하고, 진행 중 대국이 있으면 `/play/:gameId`로 이동해 `game:sync`를 보낸다.

## 8. 오류 처리

- 도메인 규칙 위반은 오류 코드가 붙은 도메인 예외로 즉시 던진다. 코드: `NOT_YOUR_TURN`, `CELL_ALREADY_OPEN`, `OUT_OF_BOARD`, `GAME_FINISHED`, `GAME_NOT_FOUND`, `NOT_A_PARTICIPANT`, `ALREADY_IN_GAME`, `ROOM_NOT_FOUND`, `ROOM_FULL`, `ROOM_EXPIRED`, `ALREADY_QUEUED`, `INVALID_SKIN`, `NICKNAME_TAKEN`, `INVALID_INPUT`, `UNAUTHORIZED`, `REMATCH_EXPIRED`, `INTERNAL`.
- 입력 검증은 inbound 어댑터에서 pydantic v2 스키마로 한다.
- 소켓 어댑터는 예외를 요청한 사람에게만 `error`로 보낸다. REST 어댑터는 Flask 오류 핸들러에서 같은 형식의 JSON과 HTTP 상태 코드로 바꾼다.
- 예상하지 못한 예외는 대국 ID와 함께 ERROR 로그로 남기고 `INTERNAL`로 응답한다. 타이머·봇·매칭 백그라운드 작업의 예외도 로그로 남기며 삼키지 않는다.
- 결과 저장이 실패하면 롤백하고, 결과 전체를 ERROR 로그에 남겨 수동 복구가 가능하게 한 뒤, 레이팅 변화를 null로 하여 `game:ended`를 보낸다.
- 서버 재시작으로 대국이 사라진 경우 `game:sync`는 `GAME_NOT_FOUND`를 받고, 클라이언트는 "서버 점검으로 대국이 종료되었습니다"를 띄운 뒤 로비로 간다. 이 대국은 기록하지 않는다.
- 테스트용 시드 설정 `WHERESMEOW_TEST_SEED`가 운영 환경에서 켜져 있으면 서버는 시작을 거부한다.

## 9. 테스트 전략

### 9.1 백엔드 단위 테스트 (pytest)

- 구조는 클래스 → 메서드 → 케이스다. 예: `class TestGame:` 안에 `class TestReveal:`.
- 테스트 이름은 성공·실패를 앞에 붙인다. 예: `test_성공_고양이를_찾으면_한번_더_둔다`, `test_실패_자기_차례가_아니면_거부한다`.
- 대상
  - game: 열기, 연쇄 열기, 득점과 한 번 더 두기, 시간 초과 -1점, 오래된 `turn_seq` 무시, 3회 연속 자동 기권, 25마리 종료, 무승부, 음수 점수, 기권, 스킨 배정, 재대결 규칙.
  - Board 생성: 고양이 수, 숫자 계산.
  - rating: Elo 계산(승, 패, 무), 랭킹 대상 조건.
  - matchmaking: 범위 확장(가짜 시계), 선착순 우선권, 중복 배정 방지.
  - room: 코드 생성 알파벳, 만료, 정원.
  - account: 아이디·비밀번호·닉네임 규칙, 토큰 rotation, 스킨 검증.
  - bot: 난이도별 판단. 답이 정해진 판을 직접 만들어 검증하고, 봇이 정답 배치를 받지 않음을 확인한다.
- 애플리케이션 서비스는 가짜 어댑터(메모리 저장소, 가짜 타이머, 가짜 이벤트 발행기, 가짜 시계)로 검증한다.

### 9.2 백엔드 통합 테스트

- Flask 테스트 클라이언트와 Flask-SocketIO 테스트 클라이언트로 REST와 소켓 흐름을 검증한다.
- DB는 SQLite 메모리 모드를 쓴다.
- 각 도메인의 테스트 아래 `integration` 패키지에 둔다. 예: `tests/game/integration/test_game_socket_flow.py`.

### 9.3 프런트엔드

- Vitest와 React Testing Library: 대국 리듀서(`version` 누락 시 `game:sync` 요청), 칸 크기 계산, 스킨 표시, 결과 화면 재대결 상태.

### 9.4 종단 간 테스트

- Playwright로 브라우저 두 개를 띄워 초대 링크로 입장해 한 판을 끝까지 둔다. `WHERESMEOW_TEST_SEED`로 고양이 배치를 고정한다.
- 화면 확인은 `ui-test` 절차의 체크리스트로 보완한다.

## 10. 범위 밖 (첫 출시 제외)

- 관전, 채팅, 친구 목록
- 다시보기 화면(수순 기록은 저장함)
- 게스트 전적을 회원 계정으로 옮기기
- 같은 이메일의 소셜 계정 연결
- 원작의 폭탄 특수 아이템
- 다국어 지원
- 수평 확장(Redis 등)

## 11. 알려진 위험

- **게스트를 이용한 레이팅 조작**: 게스트는 무료로 무한히 만들 수 있으므로, 회원이 게스트 계정을 만들어 일부러 지는 방식으로 레이팅을 올릴 수 있다. 사용자가 감수하기로 결정했다. 문제가 되면 "게스트가 포함된 대국은 회원 레이팅에 미반영" 같은 규칙으로 바꾼다.
- **같은 상대와의 반복 대국**: 모든 재대결이 레이팅에 반영되므로 두 계정 간 반복 대국으로 레이팅을 조작할 수 있다.
- **서버 재시작 시 진행 중 대국 소실**: 단일 프로세스 메모리 상태의 한계다.
- **턴 타이머 정확도**: 서버 시각 기준이므로 네트워크 지연이 큰 플레이어는 체감 시간이 조금 짧다.

## 12. 구현 단계

각 단계가 끝나면 그 시점까지의 기능이 실제로 동작해야 한다.

1. **핵심 대국**: 서버·클라이언트 골격, game 도메인, 메모리 저장소, 턴 타이머, 소켓 대국 이벤트, 게스트 신원(서명 토큰 + 메모리 저장소), 초대 방, 최소 대국 화면. 게스트 두 명이 링크로 한 판을 둘 수 있다.
2. **영속화와 계정 기반**: PostgreSQL, Alembic, players, 게스트 저장, 결과 기록, 재접속(`game:sync`, `GET /api/games/current`).
3. **화면 완성**: 고양이 스킨 10종, 들풀 칸, 발자국 숫자, A안 대국 화면, 결과 화면, 내 고양이 설정, 로비.
4. **컴퓨터 대전**: bot 도메인, 난이도 3단계, 봇 전적.
5. **회원 계정**: 자체 가입·로그인, 토큰 rotation, Google·Naver·Kakao.
6. **레이팅·매칭·랭킹**: Elo, 단일 대기열, 랭킹, 프로필.
7. **재대결**.
8. **배포 준비**: Dockerfile, docker compose, nginx 설정, Playwright E2E.
