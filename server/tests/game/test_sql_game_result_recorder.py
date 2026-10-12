from sqlalchemy import select

from fakes import FakeClock
from persistence_support import migrated_database
from wheresmeow.game.adapter.outbound.persistence.models import GameRecordRow
from wheresmeow.game.adapter.outbound.persistence.sql_game_result_recorder import SqlGameResultRecorder
from wheresmeow.game.domain.board import Board
from wheresmeow.game.domain.game import Game, GameMode, Seat


def finished_game() -> Game:
    seats = (Seat("a", "에이", 16), Seat("b", "비", 17))
    game = Game("g1", GameMode.INVITE, Board(4, frozenset({(0, 0), (3, 3)})), seats, 0, 1_000)
    game.reveal("a", 0, 0, now_ms=2_000)
    game.forfeit("b", now_ms=3_000)
    return game


class TestSqlGameResultRecorder:
    class TestRecord:
        def test_성공_끝난_대국의_결과_배치_수순을_저장한다(self):
            database = migrated_database()

            SqlGameResultRecorder(database, FakeClock(now_ms=5_000)).record(finished_game())

            with database.session() as s:
                row = s.scalars(select(GameRecordRow)).one()
            assert (row.id, row.mode, row.end_reason, row.winner_seat) == ("g1", "INVITE", "FORFEIT", 0)
            assert (row.seat0_player_id, row.seat0_nickname, row.seat0_skin, row.seat0_score) == ("a", "에이", 16, 1)
            assert (row.seat1_player_id, row.seat1_score) == ("b", 0)
            assert sorted(map(tuple, row.cats)) == [(0, 0), (3, 3)]
            assert [m["type"] for m in row.moves] == ["reveal", "forfeit"]
            assert row.bot_difficulty is None
