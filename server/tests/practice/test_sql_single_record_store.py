from persistence_support import migrated_database
from wheresmeow.practice.adapter.outbound.persistence.sql_single_record_store import SqlSingleRecordStore
from wheresmeow.practice.application.port.outbound import SingleRecord
from wheresmeow.practice.domain.record import Difficulty


class TestSqlSingleRecordStore:
    class TestRecordClear:
        def test_성공_첫_기록을_만들고_더_빠를_때만_갱신한다(self):
            store = SqlSingleRecordStore(migrated_database())

            assert store.record_clear("p", Difficulty.BEGINNER, 40_000, 1) == (SingleRecord(40_000, 1), True)
            assert store.record_clear("p", Difficulty.BEGINNER, 45_000, 2) == (SingleRecord(40_000, 2), False)
            assert store.record_clear("p", Difficulty.BEGINNER, 31_000, 3) == (SingleRecord(31_000, 3), True)

        def test_성공_플레이어와_난이도별로_따로_읽는다(self):
            store = SqlSingleRecordStore(migrated_database())
            store.record_clear("p", Difficulty.BEGINNER, 40_000, 1)
            store.record_clear("p", Difficulty.EXPERT, 400_000, 1)
            store.record_clear("q", Difficulty.BEGINNER, 10_000, 1)

            assert store.records_of("p") == {
                Difficulty.BEGINNER: SingleRecord(40_000, 1),
                Difficulty.EXPERT: SingleRecord(400_000, 1),
            }
            assert store.records_of("nobody") == {}
