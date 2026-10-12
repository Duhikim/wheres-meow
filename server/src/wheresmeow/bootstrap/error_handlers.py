import logging

from flask import Flask, jsonify
from flask_socketio import SocketIO, emit
from werkzeug.exceptions import HTTPException

from wheresmeow.shared.errors import DomainError

logger = logging.getLogger(__name__)

HTTP_STATUS_BY_CODE = {
    "INVALID_INPUT": 400,
    "UNAUTHORIZED": 401,
    "INVALID_CREDENTIALS": 401,
    "NOT_A_PARTICIPANT": 403,
    "NOT_ROOM_HOST": 403,
    "GAME_NOT_FOUND": 404,
    "ROOM_NOT_FOUND": 404,
    "PLAYER_NOT_FOUND": 404,
    "PROVIDER_DISABLED": 404,
    "ALREADY_IN_GAME": 409,
    "ALREADY_QUEUED": 409,
    "ROOM_FULL": 409,
    "USERNAME_TAKEN": 409,
    "NICKNAME_TAKEN": 409,
    "ROOM_EXPIRED": 410,
}


def error_body(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def register_http_error_handlers(app: Flask) -> None:
    @app.errorhandler(DomainError)
    def on_domain_error(error: DomainError):
        return jsonify(error_body(error.code, error.message)), HTTP_STATUS_BY_CODE.get(error.code, 400)

    @app.errorhandler(429)
    def on_rate_limited(_error):
        return jsonify(error_body("RATE_LIMITED", "요청이 너무 많습니다. 잠시 후 다시 시도해 주세요")), 429

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
