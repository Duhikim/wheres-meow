from wheresmeow.game.adapter.outbound.socket.payloads import cell_payload, event_payload, started_payload
from wheresmeow.game.domain.board import Board
from wheresmeow.game.domain.game import Game, GameMode, OpenedCell, Seat


def make_game() -> Game:
    seats = (Seat("a", "에이", 16), Seat("b", "비", 17))
    return Game("g1", GameMode.INVITE, Board(4, frozenset({(0, 0), (3, 3)})), seats, 0, 0)


class TestPayloads:
    class TestCellPayload:
        def test_성공_숫자_칸은_n을_담는다(self):
            assert cell_payload(OpenedCell(1, 2, 3, None)) == {"x": 1, "y": 2, "kind": "number", "n": 3}

        def test_성공_고양이_칸은_찾은_좌석을_담는다(self):
            assert cell_payload(OpenedCell(0, 0, None, 1)) == {"x": 0, "y": 0, "kind": "cat", "seat": 1}

    class TestStartedPayload:
        def test_성공_진행_중_페이로드에는_고양이_위치가_없다(self):
            payload = started_payload(make_game(), my_seat=1)

            assert payload["mySeat"] == 1
            assert [seat["isBot"] for seat in payload["seats"]] == [False, False]
            assert "cats" not in payload
            assert "(3, 3)" not in str(payload) and "[3, 3]" not in str(payload)

    class TestEventPayload:
        def test_성공_종료_이벤트에만_고양이_위치를_담는다(self):
            game = make_game()
            [ended] = game.forfeit("a", now_ms=0)

            name, payload = event_payload(game.id, ended)

            assert name == "game:ended"
            assert payload["cats"] == [[0, 0], [3, 3]]
            assert (payload["reason"], payload["winner"]) == ("FORFEIT", 1)

        def test_성공_공개_이벤트의_이름과_필드(self):
            game = make_game()
            [revealed] = game.reveal("a", 1, 0, now_ms=0)

            name, payload = event_payload(game.id, revealed)

            assert name == "game:revealed"
            assert payload["cells"] == [{"x": 1, "y": 0, "kind": "number", "n": 1}]
            assert payload["currentSeat"] == 1
