from collections.abc import Callable

from flask import Blueprint, jsonify

from wheresmeow.game.application.port.inbound import FindCurrentGameUseCase


def create_game_blueprint(find_current_game: FindCurrentGameUseCase, current_player_id: Callable[[], str]) -> Blueprint:
    blueprint = Blueprint("game", __name__, url_prefix="/api/games")

    @blueprint.get("/current")
    def get_current():
        """재접속용. 진행 중인 대국이 있으면 ID, 없으면 204."""
        game = find_current_game.find_current_game(current_player_id())
        if game is None:
            return "", 204
        return jsonify({"gameId": game.id})

    return blueprint
