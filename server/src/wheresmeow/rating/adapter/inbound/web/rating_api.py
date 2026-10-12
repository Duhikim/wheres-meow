from typing import Any

from flask import Blueprint, jsonify, request

from wheresmeow.rating.application.port.inbound import (
    GetProfileUseCase,
    GetRankingsUseCase,
    RatingSummary,
    RecentGame,
)
from wheresmeow.shared.errors import InvalidInput


def summary_payload(summary: RatingSummary) -> dict[str, int]:
    return {
        "rating": summary.rating,
        "games": summary.games,
        "wins": summary.wins,
        "losses": summary.losses,
        "draws": summary.draws,
    }


def recent_payload(game: RecentGame) -> dict[str, Any]:
    return {
        "gameId": game.game_id,
        "mode": game.mode,
        "endedAt": game.ended_at_ms,
        "opponentId": game.opponent_id,
        "opponentNickname": game.opponent_nickname,
        "myScore": game.my_score,
        "opponentScore": game.opponent_score,
        "result": game.result,
        "ratingBefore": game.rating_before,
        "ratingAfter": game.rating_after,
    }


def create_rating_blueprint(rankings: GetRankingsUseCase, profiles: GetProfileUseCase) -> Blueprint:
    """랭킹·프로필은 누구나 볼 수 있다(로그인 불필요)."""
    blueprint = Blueprint("rating", __name__, url_prefix="/api")

    @blueprint.get("/rankings")
    def get_rankings():
        raw = request.args.get("page", "1")
        if not raw.isdigit():
            raise InvalidInput(f"쪽 번호는 숫자여야 합니다: {raw}")
        page = rankings.rankings(int(raw))
        return jsonify({
            "page": page.page,
            "totalPages": page.total_pages,
            "entries": [
                {
                    "rank": e.rank,
                    "playerId": e.player_id,
                    "nickname": e.nickname,
                    "skin": e.skin,
                    **summary_payload(e.summary),
                }
                for e in page.entries
            ],
        })

    @blueprint.get("/players/<player_id>")
    def get_profile(player_id: str):
        profile = profiles.profile(player_id)
        return jsonify({
            "id": profile.player_id,
            "nickname": profile.nickname,
            "kind": profile.kind,
            "skin": profile.skin,
            **summary_payload(profile.rating),
            "ranked": profile.ranked,
            "recentGames": [recent_payload(g) for g in profile.recent_games],
            "botRecords": profile.bot_records,
            "singleRecords": profile.single_records,
        })

    return blueprint
