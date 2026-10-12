from sqlalchemy.orm import Session

from wheresmeow.bot.adapter.outbound.persistence.models import BotRecordRow
from wheresmeow.game.domain.game import Game, GameMode


class BotRecordContributor:
    """대국 기록과 같은 트랜잭션에서 사람 쪽의 봇 전적을 갱신한다(game 의 ResultContributor 구현)."""

    def contribute(self, session: Session, game: Game) -> None:
        if game.mode is not GameMode.BOT:
            return
        human_seat = next(i for i, seat in enumerate(game.seats) if not seat.is_bot)
        human = game.seats[human_seat]
        assert game.bot_difficulty is not None
        row = session.get(BotRecordRow, (human.player_id, game.bot_difficulty))
        if row is None:
            row = BotRecordRow(player_id=human.player_id, difficulty=game.bot_difficulty, wins=0, losses=0, draws=0)
            session.add(row)
        if game.winner is None:
            row.draws += 1
        elif game.winner == human_seat:
            row.wins += 1
        else:
            row.losses += 1
