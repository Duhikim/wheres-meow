from sqlalchemy import select

from wheresmeow.practice.adapter.outbound.persistence.models import SingleRecordRow
from wheresmeow.practice.application.port.outbound import SingleRecord
from wheresmeow.practice.domain.record import Difficulty
from wheresmeow.shared.persistence.database import Database, ms_to_datetime


class SqlSingleRecordStore:
    def __init__(self, database: Database) -> None:
        self._database = database

    def records_of(self, player_id: str) -> dict[Difficulty, SingleRecord]:
        with self._database.session() as session:
            rows = session.scalars(select(SingleRecordRow).where(SingleRecordRow.player_id == player_id)).all()
            return {Difficulty(r.difficulty): SingleRecord(r.best_ms, r.clears) for r in rows}

    def record_clear(
        self, player_id: str, difficulty: Difficulty, elapsed_ms: int, now_ms: int
    ) -> tuple[SingleRecord, bool]:
        with self._database.session() as session:
            # 같은 사람이 두 탭에서 동시에 깬 경우에도 최고 기록·횟수가 어긋나지 않게 행을 잠근다
            row = session.scalars(
                select(SingleRecordRow)
                .where(SingleRecordRow.player_id == player_id, SingleRecordRow.difficulty == difficulty.value)
                .with_for_update()
            ).first()
            if row is None:
                row = SingleRecordRow(
                    player_id=player_id, difficulty=difficulty.value, best_ms=elapsed_ms, clears=0,
                    updated_at=ms_to_datetime(now_ms),
                )
                session.add(row)
                new_best = True
            else:
                new_best = elapsed_ms < row.best_ms
                if new_best:
                    row.best_ms = elapsed_ms
            row.clears += 1
            row.updated_at = ms_to_datetime(now_ms)
            return SingleRecord(row.best_ms, row.clears), new_best
