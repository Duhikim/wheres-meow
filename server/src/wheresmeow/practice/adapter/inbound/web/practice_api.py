from collections.abc import Callable

from flask import Blueprint, jsonify, request
from pydantic import BaseModel, ConfigDict, StrictInt

from wheresmeow.practice.application.port.inbound import SingleRecordsUseCase, SubmitClearUseCase
from wheresmeow.shared.payload import parse_payload


class SubmitClearRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    difficulty: str
    elapsedMs: StrictInt


def create_practice_blueprint(
    submit: SubmitClearUseCase, records: SingleRecordsUseCase, current_player_id: Callable[[], str]
) -> Blueprint:
    blueprint = Blueprint("practice", __name__, url_prefix="/api")

    @blueprint.get("/players/me/single-records")
    def get_my_single_records():
        return jsonify(records.records(current_player_id()))

    @blueprint.post("/players/me/single-records")
    def post_single_clear():
        body = parse_payload(SubmitClearRequest, request.get_json(silent=True))
        result = submit.submit_clear(current_player_id(), body.difficulty, body.elapsedMs)
        return jsonify({
            "difficulty": result.difficulty,
            "bestMs": result.best_ms,
            "newBest": result.new_best,
            "clears": result.clears,
        })

    return blueprint
