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
