from sqlalchemy import and_, func, or_, select

from wheresmeow.account.adapter.outbound.persistence.models import PlayerRow
from wheresmeow.game.adapter.outbound.persistence.models import GameRecordRow
from wheresmeow.rating.adapter.outbound.persistence.models import RatingChangeRow, RatingRow
from wheresmeow.rating.application.port.inbound import RatingSummary, RecentGame
from wheresmeow.rating.application.port.outbound import RankedRow
from wheresmeow.shared.persistence.database import Database, datetime_to_ms

HUMAN_MODES = ("INVITE", "MATCH")


class SqlRatingReader:
    """랭킹·프로필 조회용 읽기 모델. 조회 전용이라 players·game_records 를 직접 묶어 읽는다."""

    def __init__(self, database: Database) -> None:
        self._database = database

    def count_ranked(self, min_games: int) -> int:
        with self._database.session() as session:
            return session.scalar(select(func.count()).select_from(RatingRow).join(
                PlayerRow, PlayerRow.id == RatingRow.player_id
            ).where(*self._ranked_filter(min_games)))

    def ranked(self, min_games: int, offset: int, limit: int) -> list[RankedRow]:
        query = (
            select(RatingRow, PlayerRow.nickname, PlayerRow.skin_1p)
            .join(PlayerRow, PlayerRow.id == RatingRow.player_id)
            .where(*self._ranked_filter(min_games))
            .order_by(RatingRow.rating.desc(), RatingRow.games.desc(), RatingRow.player_id)
            .offset(offset)
            .limit(limit)
        )
        with self._database.session() as session:
            return [
                RankedRow(r.player_id, nickname, skin, r.rating, r.games, r.wins, r.losses, r.draws)
                for r, nickname, skin in session.execute(query).all()
            ]

    def summary_of(self, player_id: str) -> RatingSummary | None:
        with self._database.session() as session:
            row = session.get(RatingRow, player_id)
            if row is None:
                return None
            return RatingSummary(row.rating, row.games, row.wins, row.losses, row.draws)

    def recent_games(self, player_id: str, limit: int) -> list[RecentGame]:
        query = (
            select(GameRecordRow, RatingChangeRow)
            .outerjoin(RatingChangeRow, and_(
                RatingChangeRow.game_id == GameRecordRow.id, RatingChangeRow.player_id == player_id
            ))
            .where(
                or_(GameRecordRow.seat0_player_id == player_id, GameRecordRow.seat1_player_id == player_id),
                GameRecordRow.mode.in_(HUMAN_MODES),
            )
            .order_by(GameRecordRow.ended_at.desc())
            .limit(limit)
        )
        with self._database.session() as session:
            return [self._to_recent(game, change, player_id) for game, change in session.execute(query).all()]

    @staticmethod
    def _ranked_filter(min_games: int) -> tuple:
        return PlayerRow.kind == "MEMBER", RatingRow.games >= min_games

    @staticmethod
    def _to_recent(game: GameRecordRow, change: RatingChangeRow | None, player_id: str) -> RecentGame:
        my_seat = 0 if game.seat0_player_id == player_id else 1
        seats = [
            (game.seat0_player_id, game.seat0_nickname, game.seat0_score),
            (game.seat1_player_id, game.seat1_nickname, game.seat1_score),
        ]
        opponent_id, opponent_nickname, opponent_score = seats[1 - my_seat]
        if game.winner_seat is None:
            result = "DRAW"
        else:
            result = "WIN" if game.winner_seat == my_seat else "LOSS"
        return RecentGame(
            game_id=game.id,
            mode=game.mode,
            ended_at_ms=datetime_to_ms(game.ended_at),
            opponent_id=opponent_id,
            opponent_nickname=opponent_nickname,
            my_score=seats[my_seat][2],
            opponent_score=opponent_score,
            result=result,
            rating_before=change.before if change else None,
            rating_after=change.after if change else None,
        )
