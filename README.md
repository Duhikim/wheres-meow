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

## 현재 진행 상황

설계의 8단계 중 **1단계(핵심 대국)**와 배포 구성이 들어가 있습니다. 게스트 입장, 초대 링크, 대국 규칙
전체가 동작하며, 화면은 임시 표현(단색 칸, 🐱 이모지)입니다. 고양이 스킨·들풀 화면(3단계), 저장·재접속(2단계),
컴퓨터 대전, 회원·랭킹·매칭, 재대결은 이후 단계입니다. 진행 중 대국은 서버 메모리에 있어 재배포하면 사라집니다.

## 구조

```
server/   Flask + Flask-SocketIO, 도메인별 헥사고널 구조 (game · room · account)
web/      React + Vite + TypeScript
.railway/ Railway 인프라 정의 (railway.ts)
Dockerfile 웹 빌드 후 Flask 가 API·Socket.IO·화면을 함께 제공하는 운영 이미지
```

## 로컬 실행

```bash
# 서버 (포트 5000)
cd server && python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/python -m wheresmeow

# 웹 (포트 5173, /api 와 /socket.io 를 5000 으로 프록시)
cd web && npm install && npm run dev
```

두 명을 시험하려면 `http://127.0.0.1:5173` 과 `http://localhost:5173` 처럼 출처가 다른 주소로 접속합니다.

## 테스트

```bash
cd server && .venv/bin/pytest          # 서버 단위·통합 테스트
cd web && npx vitest run               # 웹 테스트
SMOKE_BASE=http://127.0.0.1:5173 node web/scripts/smoke.mjs   # 실제 서버 대상 대국 흐름 확인
```

## 배포

`main` 에 푸시하면 Railway 가 `Dockerfile` 로 빌드해 자동 배포합니다. 설정은 `.railway/railway.ts` 에 있고,
`npm install` 후 `railway config plan` 으로 차이를 확인합니다. 필요한 환경 변수는
`WHERESMEOW_ENV=production`, `WHERESMEOW_ASYNC_MODE=gevent`, `WHERESMEOW_SECRET_KEY` 입니다.
