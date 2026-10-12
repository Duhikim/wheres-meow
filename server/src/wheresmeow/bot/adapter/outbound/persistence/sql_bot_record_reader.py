from sqlalchemy import select

from wheresmeow.bot.adapter.outbound.persistence.models import BotRecordRow
from wheresmeow.bot.domain.solver import Difficulty
from wheresmeow.shared.persistence.database import Database


class SqlBotRecordReader:
    def __init__(self, database: Database) -> None:
        self._database = database

    def records_of(self, player_id: str) -> dict[Difficulty, tuple[int, int, int]]:
        with self._database.session() as session:
            rows = session.scalars(select(BotRecordRow).where(BotRecordRow.player_id == player_id)).all()
            return {Difficulty(r.difficulty): (r.wins, r.losses, r.draws) for r in rows}
