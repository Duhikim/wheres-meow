# Where's Meow 운영 이미지. 웹을 빌드한 뒤 Flask 서버가 API·Socket.IO 와 함께 화면을 제공한다.

# 1단계: 웹 빌드
FROM node:26-slim AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY web/ ./
RUN npm run build

# 2단계: 서버
FROM python:3.14-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    WHERESMEOW_ENV=production \
    WHERESMEOW_ASYNC_MODE=gevent \
    WHERESMEOW_STATIC_DIR=/app/static
WORKDIR /app
COPY server/pyproject.toml ./server/pyproject.toml
COPY server/src ./server/src
RUN pip install --no-cache-dir ./server
COPY --from=web /web/dist ./static
EXPOSE 8080
# WHERESMEOW_SECRET_KEY 는 실행 환경(Railway 변수)에서 넣는다. 없으면 서버가 시작을 거부한다.
CMD ["python", "-m", "wheresmeow.serve"]
