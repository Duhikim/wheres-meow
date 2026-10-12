#!/bin/sh
# E2E 용 서버. 웹을 빌드한 뒤 Flask 개발 서버 하나가 화면·API·Socket.IO 를 함께 제공한다.
# 고양이 배치는 시드로 고정하고, DB 는 매번 새 SQLite 파일로 시작한다.
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd)
rm -f "$ROOT/e2e/.e2e.db"
(cd "$ROOT/web" && npm run build >/dev/null)
cd "$ROOT/server"
export PORT="${E2E_PORT:-5100}"
export WHERESMEOW_TEST_SEED="${E2E_SEED:-20261012}"
export WHERESMEOW_STATIC_DIR="$ROOT/web/dist"
export DATABASE_URL="sqlite:///$ROOT/e2e/.e2e.db"
exec .venv/bin/python -m wheresmeow
