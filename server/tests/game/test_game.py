"""Game 엔티티 테스트.

4x4 판, 고양이 위치 (0,0) (3,0) (3,3). 각 칸의 숫자는 다음과 같다(C = 고양이).

    y=0:  C 1 1 C
    y=1:  1 1 1 1
    y=2:  0 0 1 1
    y=3:  0 0 1 C
"""

import pytest

from wheresmeow.game.domain.board import Board
from wheresmeow.game.domain.errors import (
    CellAlreadyOpen,
    GameFinished,
    NotAParticipant,
    NotYourTurn,
    OutOfBoard,
)
from wheresmeow.game.domain.game import (
    TURN_MS,
    CellsRevealed,
    EndReason,
    Game,
    GameEnded,
    GameMode,
    GameStatus,
    Seat,
    TurnTimedOut,
)

CATS = frozenset({(0, 0), (3, 0), (3, 3)})
A, B = "player-a", "player-b"


def make_game(first_seat: int = 0, now_ms: int = 0) -> Game:
    seats = (Seat(A, "에이", 16), Seat(B, "비", 17))
    return Game("g1", GameMode.INVITE, Board(4, CATS), seats, first_seat, now_ms)


class TestGame:
    class TestInit:
        def test_성공_선공_좌석의_턴으로_시작한다(self):
            game = make_game(first_seat=1, now_ms=500)

            assert game.current_seat == 1
            assert game.turn_seq == 1
            assert game.turn_deadline_ms == 500 + TURN_MS
            assert game.version == 0

        def test_실패_같은_플레이어가_두_좌석에_앉으면_거부한다(self):
            with pytest.raises(ValueError):
                Game("g", GameMode.INVITE, Board(4, CATS), (Seat(A, "a", 16), Seat(A, "a", 17)), 0, 0)

    class TestReveal:
        def test_성공_고양이를_찾으면_1점을_얻고_한번_더_둔다(self):
            game = make_game()

            events = game.reveal(A, 0, 0, now_ms=1000)

            assert game.scores == (1, 0)
            assert game.current_seat == 0
            assert game.turn_seq == 2
            assert game.turn_deadline_ms == 1000 + TURN_MS
            [event] = events
            assert isinstance(event, CellsRevealed)
            assert event.cells[0].found_by == 0
            assert event.cells[0].number is None

        def test_성공_숫자_칸이면_그_칸만_열고_턴이_넘어간다(self):
            game = make_game()

            [event] = game.reveal(A, 1, 0, now_ms=0)

            assert [(c.x, c.y, c.number) for c in event.cells] == [(1, 0, 1)]
            assert game.current_seat == 1
            assert event.current_seat == 1

        def test_성공_빈_칸이면_연결된_영역을_열되_고양이는_열지_않는다(self):
            game = make_game()

            [event] = game.reveal(A, 0, 3, now_ms=0)

            opened = {(c.x, c.y) for c in event.cells}
            assert opened == {(0, 3), (1, 3), (0, 2), (1, 2), (2, 3), (2, 2), (0, 1), (1, 1), (2, 1)}
            assert opened.isdisjoint(CATS)
            assert game.current_seat == 1

        def test_성공_정상_수를_두면_연속_시간_초과_횟수가_초기화된다(self):
            game = make_game()
            game.timeout(game.turn_seq, now_ms=0)  # A 초과 → B 차례
            game.reveal(B, 1, 0, now_ms=0)  # B 숫자 → A 차례

            game.reveal(A, 2, 0, now_ms=0)

            assert game.seats[0].consecutive_timeouts == 0

        def test_성공_마지막_고양이를_찾으면_점수가_높은_쪽이_이기고_끝난다(self):
            game = make_game()
            game.reveal(A, 0, 0, now_ms=0)
            game.reveal(A, 3, 0, now_ms=0)

            events = game.reveal(A, 3, 3, now_ms=0)

            revealed, ended = events
            assert isinstance(revealed, CellsRevealed)
            assert revealed.turn_deadline_ms is None
            assert isinstance(ended, GameEnded)
            assert ended.reason is EndReason.ALL_FOUND
            assert ended.winner == 0
            assert ended.scores == (3, 0)
            assert set(ended.cats) == CATS
            assert game.status is GameStatus.FINISHED

        def test_성공_마지막_고양이를_찾았을_때_동점이면_무승부다(self):
            game = make_game()
            game.reveal(A, 0, 0, now_ms=0)  # A 1:0
            game.timeout(game.turn_seq, now_ms=0)  # A 0:0 → B 차례
            game.reveal(B, 3, 0, now_ms=0)  # B 0:1
            game.reveal(B, 2, 0, now_ms=0)  # B 숫자 → A 차례

            _, ended = game.reveal(A, 3, 3, now_ms=0)  # A 1:1

            assert ended.winner is None
            assert ended.scores == (1, 1)

        def test_성공_이벤트마다_version이_1씩_증가한다(self):
            game = make_game()
            game.reveal(A, 0, 0, now_ms=0)
            game.reveal(A, 3, 0, now_ms=0)

            revealed, ended = game.reveal(A, 3, 3, now_ms=0)

            assert (revealed.version, ended.version) == (3, 4)
            assert game.version == 4

        def test_실패_자기_차례가_아니면_거부한다(self):
            with pytest.raises(NotYourTurn):
                make_game().reveal(B, 1, 0, now_ms=0)

        def test_실패_이미_열린_칸이면_거부한다(self):
            game = make_game()
            game.reveal(A, 0, 0, now_ms=0)

            with pytest.raises(CellAlreadyOpen):
                game.reveal(A, 0, 0, now_ms=0)

        def test_실패_판_밖이면_거부한다(self):
            with pytest.raises(OutOfBoard):
                make_game().reveal(A, 4, 0, now_ms=0)

        def test_실패_참가자가_아니면_거부한다(self):
            with pytest.raises(NotAParticipant):
                make_game().reveal("stranger", 1, 0, now_ms=0)

        def test_실패_끝난_대국이면_거부한다(self):
            game = make_game()
            game.forfeit(B, now_ms=0)

            with pytest.raises(GameFinished):
                game.reveal(A, 1, 0, now_ms=0)

    class TestTimeout:
        def test_성공_1점을_잃고_턴이_넘어간다(self):
            game = make_game()

            [event] = game.timeout(game.turn_seq, now_ms=2000)

            assert isinstance(event, TurnTimedOut)
            assert event.seat == 0
            assert event.scores == (-1, 0)
            assert event.current_seat == 1
            assert event.turn_deadline_ms == 2000 + TURN_MS

        def test_성공_점수는_음수가_될_수_있다(self):
            game = make_game()
            game.timeout(game.turn_seq, now_ms=0)
            game.timeout(game.turn_seq, now_ms=0)
            game.timeout(game.turn_seq, now_ms=0)

            assert game.scores == (-2, -1)

        def test_성공_지나간_턴의_타이머는_무시한다(self):
            game = make_game()
            stale = game.turn_seq
            game.reveal(A, 1, 0, now_ms=0)

            assert game.timeout(stale, now_ms=0) == []
            assert game.scores == (0, 0)

        def test_성공_같은_플레이어가_3회_연속_초과하면_자동_기권패다(self):
            game = make_game()
            for _ in range(4):  # A, B, A, B 각각 초과
                game.timeout(game.turn_seq, now_ms=0)

            timed_out, ended = game.timeout(game.turn_seq, now_ms=0)  # A 세 번째

            assert timed_out.seat == 0
            assert timed_out.turn_deadline_ms is None
            assert ended.reason is EndReason.AUTO_FORFEIT
            assert ended.winner == 1

    class TestForfeit:
        def test_성공_점수와_관계없이_기권한_쪽이_진다(self):
            game = make_game()
            game.reveal(A, 0, 0, now_ms=0)  # A 1:0

            [ended] = game.forfeit(A, now_ms=0)

            assert ended.reason is EndReason.FORFEIT
            assert ended.winner == 1

        def test_성공_자기_차례가_아니어도_기권할_수_있다(self):
            [ended] = make_game().forfeit(B, now_ms=0)

            assert ended.winner == 0

        def test_실패_끝난_대국이면_거부한다(self):
            game = make_game()
            game.forfeit(A, now_ms=0)

            with pytest.raises(GameFinished):
                game.forfeit(B, now_ms=0)
