from fakes import FakeClock
from wheresmeow.game.adapter.outbound.memory.in_memory_game_store import FINISHED_RETENTION_MS, InMemoryGameStore
from wheresmeow.game.domain.board import Board
from wheresmeow.game.domain.game import Game, GameMode, Seat


def game(game_id: str, a: str = "a", b: str = "b") -> Game:
    return Game(game_id, GameMode.INVITE, Board(4, frozenset({(0, 0)})), (Seat(a, a, 16), Seat(b, b, 17)), 0, 0)


class TestInMemoryGameStore:
    class TestFindActive:
        def test_성공_진행_중인_대국을_플레이어로_찾는다(self):
            store = InMemoryGameStore(FakeClock())
            store.save(game("g1"))

            assert store.find_active_by_player("b").id == "g1"
            assert store.find_active_by_player("c") is None

        def test_성공_끝난_대국은_진행_중으로_찾지_않는다(self):
            store = InMemoryGameStore(FakeClock())
            g = game("g1")
            store.save(g)
            g.forfeit("a", now_ms=1)

            store.save(g)

            assert store.find_active_by_player("a") is None
            assert store.get("g1") is g  # 결과 화면을 위해 남아 있다

    class TestRetention:
        def test_성공_끝난_대국은_보관_시간이_지나면_지운다(self):
            clock = FakeClock(now_ms=0)
            store = InMemoryGameStore(clock)
            g = game("g1")
            store.save(g)
            g.forfeit("a", now_ms=1)
            store.save(g)

            clock.advance(FINISHED_RETENTION_MS)
            store.save(game("g2", "c", "d"))  # 저장할 때 오래된 대국을 정리한다

            assert store.get("g1") is None
            assert store.get("g2") is not None

        def test_성공_보관_시간_전에는_남겨_둔다(self):
            clock = FakeClock(now_ms=0)
            store = InMemoryGameStore(clock)
            g = game("g1")
            store.save(g)
            g.forfeit("a", now_ms=1)
            store.save(g)

            clock.advance(FINISHED_RETENTION_MS - 1)
            store.save(game("g2", "c", "d"))

            assert store.get("g1") is g

        def test_성공_진행_중인_대국은_오래되어도_지우지_않는다(self):
            clock = FakeClock(now_ms=0)
            store = InMemoryGameStore(clock)
            store.save(game("g1"))

            clock.advance(FINISHED_RETENTION_MS * 10)
            store.save(game("g2", "c", "d"))

            assert store.get("g1") is not None
