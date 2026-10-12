from collections.abc import Callable

from flask import Blueprint, jsonify

from wheresmeow.bot.application.service.bot_service import BotService


def create_bot_blueprint(bots: BotService, current_player_id: Callable[[], str]) -> Blueprint:
    blueprint = Blueprint("bot", __name__, url_prefix="/api")

    @blueprint.get("/players/me/bot-records")
    def get_my_bot_records():
        return jsonify(bots.bot_records(current_player_id()))

    return blueprint
