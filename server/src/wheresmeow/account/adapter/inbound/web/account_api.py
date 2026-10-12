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
