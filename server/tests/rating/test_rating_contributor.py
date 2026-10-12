import pytest
from sqlalchemy import select

from fakes import FakeClock
from persistence_support import migrated_database
from wheresmeow.game.adapter.outbound.persistence.models import GameRecordRow
from wheresmeow.game.adapter.outbound.persistence.sql_game_result_recorder import SqlGameResultRecorder
from wheresmeow.game.domain.board import Board
from wheresmeow.game.domain.game import Game, GameMode, RatingChange, Seat
from wheresmeow.rating.adapter.outbound.persistence.models import RatingChangeRow, RatingRow
from wheresmeow.rating.adapter.outbound.persistence.rating_contributor import RatingContributor

CATS = frozenset({(0, 0), (3, 3)})


def human_game(game_id: str, loser: str | None, mode: GameMode = GameMode.INVITE) -> Game:
    """loser 가 None 이면 두 마리를 하나씩 찾아 1:1 무승부로 끝낸다."""
    seats = (Seat("a", "에이", 16), Seat("b", "비", 17))
    game = Game(game_id, mode, Board(4, CATS), seats, 0, 0)
    if loser is None:
        game.reveal("a", 0, 0, now_ms=1)  # 고양이 → 한 번 더
        game.reveal("a", 1, 1, now_ms=2)  # 숫자 → 턴 넘김
        game.reveal("b", 3, 3, now_ms=3)  # 마지막 고양이 → 1:1 종료
    else:
        game.forfeit(loser, now_ms=1)
    return game


def recorder(database) -> SqlGameResultRecorder:
    return SqlGameResultRecorder(database, FakeClock(), contributors=[RatingContributor(FakeClock(now_ms=9))])


def rating_of(database, player_id: str) -> RatingRow:
    with database.session() as s:
        return s.get(RatingRow, player_id)


class TestRatingContributor:
    class TestHumanGame:
        def test_성공_처음_대국이면_1000에서_시작해_이긴_쪽은_오르고_진_쪽은_내린다(self):
            database = migrated_database()

            changes = recorder(database).record(human_game("g1", loser="b"))

            assert changes == (RatingChange(1000, 1016), RatingChange(1000, 984))
            a, b = rating_of(database, "a"), rating_of(database, "b")
            assert (a.rating, a.games, a.wins, a.losses, a.draws) == (1016, 1, 1, 0, 0)
            assert (b.rating, b.games, b.wins, b.losses, b.draws) == (984, 1, 0, 1, 0)

        def test_성공_다음_대국은_저장된_레이팅에서_계산한다(self):
            database = migrated_database()
            recorder(database).record(human_game("g1", loser="b"))

            changes = recorder(database).record(human_game("g2", loser="a"))

            assert changes[0].before == 1016 and changes[1].before == 984
            assert rating_of(database, "a").games == 2

        def test_성공_무승부를_센다(self):
            database = migrated_database()

            changes = recorder(database).record(human_game("g1", loser=None))

            assert changes == (RatingChange(1000, 1000), RatingChange(1000, 1000))
            assert rating_of(database, "a").draws == 1

        def test_성공_대국별로_두_사람의_변화를_rating_changes_에_남긴다(self):
            database = migrated_database()

            recorder(database).record(human_game("g1", loser="b", mode=GameMode.MATCH))

            with database.session() as s:
                rows = s.scalars(select(RatingChangeRow).order_by(RatingChangeRow.player_id)).all()
                assert [(r.game_id, r.player_id, r.before, r.after) for r in rows] == [
                    ("g1", "a", 1000, 1016),
                    ("g1", "b", 1000, 984),
                ]

    class TestBotGame:
        def test_성공_컴퓨터_대전은_레이팅에_반영하지_않고_None을_돌려준다(self):
            database = migrated_database()
            seats = (Seat("a", "에이", 16), Seat("bot:EASY", "컴퓨터", 17, is_bot=True))
            game = Game("g1", GameMode.BOT, Board(4, CATS), seats, 0, 0, bot_difficulty="EASY")
            game.forfeit("bot:EASY", now_ms=1)

            assert recorder(database).record(game) is None
            assert rating_of(database, "a") is None

    class TestTransaction:
        def test_실패_레이팅_갱신이_실패하면_대국_기록도_남기지_않는다(self):
            database = migrated_database()

            class Broken:
                def contribute(self, session, game):
                    raise RuntimeError("boom")

            broken = SqlGameResultRecorder(database, FakeClock(), contributors=[RatingContributor(FakeClock()), Broken()])
            with pytest.raises(RuntimeError):
                broken.record(human_game("g1", loser="b"))

            with database.session() as s:
                assert s.scalars(select(GameRecordRow)).all() == []
                assert s.scalars(select(RatingRow)).all() == []
                assert s.scalars(select(RatingChangeRow)).all() == []

        def test_실패_두_기여자가_모두_레이팅_변화를_돌려주면_거부한다(self):
            database = migrated_database()
            twice = SqlGameResultRecorder(
                database, FakeClock(), contributors=[RatingContributor(FakeClock()), RatingContributor(FakeClock())]
            )

            with pytest.raises(ValueError):
                twice.record(human_game("g1", loser="b"))
