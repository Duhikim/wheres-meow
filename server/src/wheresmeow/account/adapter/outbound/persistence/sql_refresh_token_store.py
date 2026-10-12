from datetime import UTC

from sqlalchemy import update

from wheresmeow.account.adapter.outbound.persistence.models import RefreshTokenRow
from wheresmeow.account.application.port.outbound import RefreshRecord
from wheresmeow.shared.persistence.database import Database, ms_to_datetime


def _to_ms(value) -> int:
    if value.tzinfo is None:  # SQLite 는 시간대 정보를 버리고 돌려준다. 저장할 때 UTC 였다.
        value = value.replace(tzinfo=UTC)
    return int(value.timestamp() * 1000)


class SqlRefreshTokenStore:
    def __init__(self, database: Database) -> None:
        self._database = database

    def save(self, record: RefreshRecord) -> None:
        with self._database.session() as session:
            session.add(
                RefreshTokenRow(
                    token_hash=record.token_hash,
                    player_id=record.player_id,
                    expires_at=ms_to_datetime(record.expires_at_ms),
                    revoked_at=None if record.revoked_at_ms is None else ms_to_datetime(record.revoked_at_ms),
                )
            )

    def find(self, token_hash: str) -> RefreshRecord | None:
        with self._database.session() as session:
            row = session.get(RefreshTokenRow, token_hash)
            if row is None:
                return None
            revoked = None if row.revoked_at is None else _to_ms(row.revoked_at)
            return RefreshRecord(row.token_hash, row.player_id, _to_ms(row.expires_at), revoked)

    def revoke(self, token_hash: str, now_ms: int) -> bool:
        """아직 폐기되지 않았을 때만 폐기하고 True. 이미 누가 폐기했으면 False(한 문장으로 원자적으로 판정)."""
        with self._database.session() as session:
            result = session.execute(
                update(RefreshTokenRow)
                .where(RefreshTokenRow.token_hash == token_hash, RefreshTokenRow.revoked_at.is_(None))
                .values(revoked_at=ms_to_datetime(now_ms))
            )
            return result.rowcount == 1

    def revoke_all(self, player_id: str, now_ms: int) -> None:
        with self._database.session() as session:
            session.execute(
                update(RefreshTokenRow)
                .where(RefreshTokenRow.player_id == player_id, RefreshTokenRow.revoked_at.is_(None))
                .values(revoked_at=ms_to_datetime(now_ms))
            )
