from wheresmeow.account.adapter.outbound.persistence.models import PlayerRow
from wheresmeow.account.domain.player import Player, PlayerKind
from wheresmeow.shared.clock import Clock
from wheresmeow.shared.persistence.database import Database, ms_to_datetime


class SqlPlayerStore:
    """PlayerStore 포트의 DB 구현. 저장할 때마다 last_seen_at 을 갱신한다."""

    def __init__(self, database: Database, clock: Clock) -> None:
        self._database = database
        self._clock = clock

    def save(self, player: Player) -> None:
        now = ms_to_datetime(self._clock.now_ms())
        with self._database.session() as session:
            row = session.get(PlayerRow, player.id)
            if row is None:
                row = PlayerRow(id=player.id, created_at=now)
                session.add(row)
            row.kind = player.kind.value
            row.nickname = player.nickname
            row.skin_1p = player.skin_1p
            row.skin_2p = player.skin_2p
            row.needs_nickname = player.needs_nickname
            row.last_seen_at = now

    def get(self, player_id: str) -> Player | None:
        with self._database.session() as session:
            row = session.get(PlayerRow, player_id)
            return None if row is None else to_player(row)


def to_player(row: PlayerRow) -> Player:
    return Player(row.id, PlayerKind(row.kind), row.nickname, row.skin_1p, row.skin_2p, bool(row.needs_nickname))
