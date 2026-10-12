from fakes import FakeClock
from persistence_support import migrated_database
from wheresmeow.account.adapter.outbound.persistence.sql_player_store import SqlPlayerStore
from wheresmeow.account.domain.player import Player, PlayerKind


class TestSqlPlayerStore:
    class TestSaveAndGet:
        def test_성공_저장한_플레이어를_그대로_읽는다(self):
            store = SqlPlayerStore(migrated_database(), FakeClock())

            store.save(Player("p1", PlayerKind.GUEST, "냥냥이", 9, 12))

            assert store.get("p1") == Player("p1", PlayerKind.GUEST, "냥냥이", 9, 12)

        def test_성공_다시_저장하면_바뀐_값으로_갱신한다(self):
            store = SqlPlayerStore(migrated_database(), FakeClock())
            player = Player("p1", PlayerKind.GUEST, "냥냥이")
            store.save(player)

            player.change_skins(20, 21)
            store.save(player)

            assert (store.get("p1").skin_1p, store.get("p1").skin_2p) == (20, 21)

        def test_성공_없는_플레이어면_None_이다(self):
            assert SqlPlayerStore(migrated_database(), FakeClock()).get("ghost") is None

        def test_성공_다른_저장소_객체로_읽어도_같다_재시작_후에도_유지(self):
            database = migrated_database()
            SqlPlayerStore(database, FakeClock()).save(Player("p1", PlayerKind.GUEST, "냥냥이"))

            assert SqlPlayerStore(database, FakeClock()).get("p1").nickname == "냥냥이"
