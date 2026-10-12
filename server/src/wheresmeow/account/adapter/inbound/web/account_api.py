from collections.abc import Callable
from typing import Any

from flask import Blueprint, jsonify, request
from pydantic import BaseModel, ConfigDict, StrictInt

from wheresmeow.account.application.port.inbound import ChangeSkinsUseCase, CreateGuestUseCase, IssueTokenUseCase
from wheresmeow.account.domain.player import Player
from wheresmeow.shared.payload import parse_payload


class CreateGuestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nickname: str


class ChangeSkinsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    skin1p: StrictInt
    skin2p: StrictInt


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
    change_skins: ChangeSkinsUseCase,
    issue_token: IssueTokenUseCase,
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
        me = current_player()
        return jsonify({**player_payload(me), "token": issue_token.issue_token(me.id)})

    @blueprint.put("/players/me/skins")
    def put_my_skins():
        me = current_player()  # 인증 실패(401)가 입력 검증(400)보다 먼저다
        body = parse_payload(ChangeSkinsRequest, request.get_json(silent=True))
        player = change_skins.change_skins(me.id, body.skin1p, body.skin2p)
        return jsonify(player_payload(player))

    return blueprint
