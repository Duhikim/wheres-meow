from sqlalchemy import select
from sqlalchemy.orm import Session

from wheresmeow.game.domain.game import Game, GameMode, RatingChange
from wheresmeow.rating.adapter.outbound.persistence.models import RatingChangeRow, RatingRow
from wheresmeow.rating.domain.elo import INITIAL_RATING, Outcome, rate
from wheresmeow.shared.clock import Clock
from wheresmeow.shared.persistence.database import ms_to_datetime


class RatingContributor:
    """대국 기록과 같은 트랜잭션에서 두 사람의 레이팅을 갱신한다(game 의 ResultContributor 구현).

    사람 간 대국(초대·매칭·재대결)만 반영하고 컴퓨터 대전은 건너뛴다(스펙 4.5·4.6).
    """

    def __init__(self, clock: Clock) -> None:
        self._clock = clock

    def contribute(self, session: Session, game: Game) -> tuple[RatingChange, RatingChange] | None:
        if game.mode is GameMode.BOT:
            return None
        rows = (self._row_for_update(session, game.seats[0].player_id),
                self._row_for_update(session, game.seats[1].player_id))
        outcome = {0: Outcome.FIRST_WINS, 1: Outcome.SECOND_WINS, None: Outcome.DRAW}[game.winner]
        befores = (rows[0].rating, rows[1].rating)
        afters = rate(befores[0], befores[1], outcome)
        now = ms_to_datetime(self._clock.now_ms())
        for index, row in enumerate(rows):
            row.rating = afters[index]
            row.games += 1
            if game.winner is None:
                row.draws += 1
            elif game.winner == index:
                row.wins += 1
            else:
                row.losses += 1
            row.updated_at = now
            session.add(RatingChangeRow(
                game_id=game.id, player_id=row.player_id, before=befores[index], after=afters[index]
            ))
        return RatingChange(befores[0], afters[0]), RatingChange(befores[1], afters[1])

    def _row_for_update(self, session: Session, player_id: str) -> RatingRow:
        # 한 사람은 대국 하나에만 앉으므로 경합은 드물지만, 읽고 쓰는 사이에 다른 갱신이 끼지 않게 행을 잠근다
        row = session.scalars(select(RatingRow).where(RatingRow.player_id == player_id).with_for_update()).first()
        if row is None:
            row = RatingRow(
                player_id=player_id, rating=INITIAL_RATING, games=0, wins=0, losses=0, draws=0,
                updated_at=ms_to_datetime(self._clock.now_ms()),
            )
            session.add(row)
        return row
