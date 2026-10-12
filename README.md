# Where's Meow

모바일 브라우저에서도 즐기는 1:1 고양이 찾기 대전 게임입니다. 두 사람이 12×12 들판을 번갈아 열며
풀숲에 숨은 고양이 25마리를 찾고, 더 많이 찾은 쪽이 이깁니다(지뢰찾기 Flags 규칙 기반).

- 서비스: https://web-production-4c3e0.up.railway.app
- 설계: [docs/superpowers/specs/2026-10-12-wheres-meow-design.md](docs/superpowers/specs/2026-10-12-wheres-meow-design.md)

## 규칙 요약

- 고양이를 찾으면 +1점, 같은 사람이 한 번 더 둡니다.
- 숫자 칸·빈 칸이면 차례가 넘어갑니다. 빈 칸은 연결된 영역이 한꺼번에 열립니다.
- 턴당 20초. 시간을 넘기면 -1점과 함께 차례가 넘어가고, 3회 연속이면 자동 기권패입니다.
- 25마리를 모두 찾거나 기권하면 끝납니다. 동점이면 무승부입니다.

## 기능

- **대국 방식**: 빠른 대전(레이팅이 비슷한 상대와 자동 매칭), 친구와 대결(초대 링크·방 코드), 컴퓨터와 대결(쉬움·보통·어려움)
- **재대결**: 결과 화면에서 신청·수락·거절. 같은 두 사람·같은 고양이로 선공만 바꿔 다시 둡니다. 30초가 지나거나 상대가 결과 화면을 떠나면 취소됩니다.
- **레이팅**: Elo(초기 1000, K=32). 사람끼리 둔 모든 대국에 반영되고, 게스트도 임시 레이팅을 가집니다. 컴퓨터 대전은 따로 전적만 셉니다.
- **랭킹·프로필**: 회원이면서 레이팅 대국 5판 이상인 사람이 랭킹에 오릅니다. 프로필에서 레이팅, 승패, 최근 20판, 컴퓨터 대전 전적을 봅니다.
- **계정**: 게스트(닉네임만), 자체 가입·로그인, Google·Naver·Kakao 소셜 로그인(키를 등록한 제공자만 켜짐)
- **내 고양이**: 고양이 10종 중 1P·2P를 골라 둡니다. 두 사람의 1P가 같으면 우선권이 없는 쪽이 2P를 씁니다.
- **재접속**: 새로고침하거나 연결이 끊겨도 진행 중인 대국으로 돌아옵니다. 진행 중 대국은 서버 메모리에 있어 재배포하면 사라집니다.

## 구조

```
server/      Flask + Flask-SocketIO, 도메인별 헥사고널 구조
             (game · room · matchmaking · rating · account · bot)
web/         React + Vite + TypeScript
e2e/         Playwright 종단 간 테스트(브라우저 두 개로 실제 서버를 상대)
.railway/    Railway 인프라 정의(railway.ts)
Dockerfile   웹을 빌드한 뒤 Flask 가 API·Socket.IO·화면을 함께 제공하는 운영 이미지
compose.yaml 운영과 같은 구성(앱 + PostgreSQL)을 로컬에서 띄우는 설정
```

## 로컬 실행

```bash
# 서버 (포트 5000, 개발용 SQLite 파일 server/wheresmeow-dev.db)
cd server && python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/python -m wheresmeow

# 웹 (포트 5173, /api 와 /socket.io 를 5000 으로 프록시)
cd web && npm install && npm run dev
```

두 명을 시험하려면 `http://127.0.0.1:5173` 과 `http://localhost:5173` 처럼 출처가 다른 주소로 접속하거나,
브라우저의 시크릿 창을 하나 더 엽니다.

운영과 같은 구성(PostgreSQL, gevent)으로 띄우려면 `docker compose up --build` 후 `http://127.0.0.1:8080` 에 접속합니다.

## 테스트

```bash
server/.venv/bin/pytest -c server/pyproject.toml server/tests   # 서버 단위·통합 테스트
cd web && npx vitest run                                         # 웹 테스트
cd e2e && npm install && npx playwright test                     # 종단 간 테스트
```

종단 간 테스트는 웹을 빌드하고 시험용 서버(포트 5100, 고양이 배치 시드 고정, 새 SQLite 파일)를 직접 띄웁니다.
설치된 Chrome 을 쓰며, Chrome 이 없는 환경에서는 `npx playwright install chromium` 후 `E2E_CHANNEL= npx playwright test` 로 돌립니다.
이미 떠 있는 서버를 상대하려면 `E2E_BASE=http://127.0.0.1:8080 npx playwright test` 처럼 주소를 줍니다
(이때는 시드가 필요한 "한 판 끝까지" 시나리오를 건너뜁니다).

## 배포

`main` 에 푸시하면 Railway 가 `Dockerfile` 로 빌드해 자동 배포합니다. 설정은 `.railway/railway.ts` 에 있고,
루트에서 `npm install` 후 `npm run railway:plan` 으로 실제 설정과의 차이를 확인합니다.

| 환경 변수 | 설명 |
|---|---|
| `WHERESMEOW_ENV=production` | 운영 모드(아래 조건을 검사하고, 어긋나면 시작을 거부) |
| `WHERESMEOW_ASYNC_MODE=gevent` | 운영은 gevent 단일 프로세스 |
| `WHERESMEOW_SECRET_KEY` | 토큰 서명 키, 32바이트 이상 |
| `DATABASE_URL` | PostgreSQL 주소(Railway 의 Postgres 서비스를 참조) |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` 등 | 소셜 로그인 키. 아래 참고 |

### 소셜 로그인 켜기

제공자마다 개발자 콘솔에서 앱을 만들고, 리디렉션(콜백) 주소에 다음을 등록한 뒤 키를 Railway 변수로 넣습니다.
키가 있는 제공자만 로그인 화면에 버튼이 나타납니다.

| 제공자 | 콘솔 | 콜백 주소 | 변수 |
|---|---|---|---|
| Google | Google Cloud Console → API 및 서비스 → 사용자 인증 정보 → OAuth 클라이언트 ID(웹 애플리케이션) | `https://<도메인>/api/auth/oauth/google/callback` | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` |
| Naver | 네이버 개발자 센터 → 애플리케이션 등록(네이버 로그인, 웹 서비스) | `https://<도메인>/api/auth/oauth/naver/callback` | `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET` |
| Kakao | Kakao Developers → 내 애플리케이션 → 카카오 로그인 활성화, 보안 → Client Secret 사용 | `https://<도메인>/api/auth/oauth/kakao/callback` | `KAKAO_CLIENT_ID`(REST API 키), `KAKAO_CLIENT_SECRET` |

지금 도메인은 `web-production-4c3e0.up.railway.app` 입니다. 변수를 넣으면 Railway 가 다시 배포합니다.
