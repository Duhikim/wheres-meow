from sqlalchemy import select

from fakes import FakeClock
from persistence_support import migrated_database
from wheresmeow.bot.adapter.outbound.persistence.bot_record_contributor import BotRecordContributor
from wheresmeow.bot.adapter.outbound.persistence.models import BotRecordRow
from wheresmeow.bot.adapter.outbound.persistence.sql_bot_record_reader import SqlBotRecordReader
from wheresmeow.bot.domain.solver import Difficulty
from wheresmeow.game.adapter.outbound.persistence.models import GameRecordRow
from wheresmeow.game.adapter.outbound.persistence.sql_game_result_recorder import SqlGameResultRecorder
from wheresmeow.game.domain.board import Board
from wheresmeow.game.domain.game import Game, GameMode, Seat


def bot_game(game_id: str, loser: str) -> Game:
    seats = (Seat("human", "사람냥", 16), Seat("bot:HARD", "컴퓨터", 17, is_bot=True))
    mode = GameMode.BOT
    game = Game(game_id, mode, Board(4, frozenset({(0, 0), (3, 3)})), seats, 0, 0, bot_difficulty="HARD")
    game.forfeit(loser, now_ms=1)
    return game


class TestBotRecordContributor:
    class TestContribute:
        def test_성공_봇_대국이_끝나면_사람의_난이도별_승패를_누적한다(self):
            database = migrated_database()
            recorder = SqlGameResultRecorder(database, FakeClock(), contributors=[BotRecordContributor()])

            recorder.record(bot_game("g1", loser="bot:HARD"))
            recorder.record(bot_game("g2", loser="human"))
            recorder.record(bot_game("g3", loser="bot:HARD"))

            assert SqlBotRecordReader(database).records_of("human") == {Difficulty.HARD: (2, 1, 0)}

        def test_성공_사람끼리의_대국은_봇_전적에_넣지_않는다(self):
            database = migrated_database()
            seats = (Seat("a", "a", 16), Seat("b", "b", 17))
            game = Game("g", GameMode.INVITE, Board(4, frozenset({(0, 0)})), seats, 0, 0)
            game.forfeit("a", now_ms=1)

            SqlGameResultRecorder(database, FakeClock(), contributors=[BotRecordContributor()]).record(game)

            with database.session() as s:
                assert s.scalars(select(BotRecordRow)).all() == []

        def test_성공_전적_갱신이_실패하면_대국_기록도_남기지_않는다_같은_트랜잭션(self):
            database = migrated_database()

            class Broken:
                def contribute(self, session, game):
                    raise RuntimeError("boom")

            recorder = SqlGameResultRecorder(database, FakeClock(), contributors=[BotRecordContributor(), Broken()])
            try:
                recorder.record(bot_game("g1", loser="human"))
            except RuntimeError:
                pass

            with database.session() as s:
                assert s.scalars(select(GameRecordRow)).all() == []
                assert s.scalars(select(BotRecordRow)).all() == []
