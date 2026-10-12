"""대국 도메인 객체를 클라이언트로 보내는 JSON 으로 바꾼다.

고양이 위치는 game:ended 에서만 내보낸다. 진행 중 페이로드에 board 를 넣지 말 것.
"""

from typing import Any

from wheresmeow.game.domain.game import (
    CellsRevealed,
    Game,
    GameEnded,
    GameEvent,
    GameStatus,
    OpenedCell,
    TurnTimedOut,
)


def cell_payload(cell: OpenedCell) -> dict[str, Any]:
    if cell.found_by is not None:
        return {"x": cell.x, "y": cell.y, "kind": "cat", "seat": cell.found_by}
    return {"x": cell.x, "y": cell.y, "kind": "number", "n": cell.number}


def started_payload(game: Game, my_seat: int) -> dict[str, Any]:
    return {
        "gameId": game.id,
        "mode": game.mode.value,
        "mySeat": my_seat,
        "seats": [
            {"nickname": s.nickname, "skin": s.skin, "score": s.score, "isBot": s.is_bot} for s in game.seats
        ],
        "currentSeat": game.current_seat,
        "turnDeadline": game.turn_deadline_ms,
        "version": game.version,
        "cells": [cell_payload(c) for c in game.opened.values()],
    }


def snapshot_payload(game: Game, my_seat: int) -> dict[str, Any]:
    """game:sync 응답(game:state). 끝난 대국일 때만 결과와 고양이 위치를 넣는다."""
    payload = started_payload(game, my_seat)
    payload["status"] = game.status.value
    payload["timeouts"] = [seat.consecutive_timeouts for seat in game.seats]
    if game.status is GameStatus.FINISHED:
        assert game.end_reason is not None
        payload["result"] = {"reason": game.end_reason.value, "winner": game.winner}
        payload["cats"] = [[x, y] for x, y in sorted(game.board.cats)]
    else:
        payload["result"] = None
    return payload


def event_payload(game_id: str, event: GameEvent) -> tuple[str, dict[str, Any]]:
    match event:
        case CellsRevealed():
            return "game:revealed", {
                "gameId": game_id,
                "seat": event.seat,
                "cells": [cell_payload(c) for c in event.cells],
                "scores": list(event.scores),
                "currentSeat": event.current_seat,
                "turnDeadline": event.turn_deadline_ms,
                "version": event.version,
            }
        case TurnTimedOut():
            return "game:timeout", {
                "gameId": game_id,
                "seat": event.seat,
                "scores": list(event.scores),
                "currentSeat": event.current_seat,
                "turnDeadline": event.turn_deadline_ms,
                "version": event.version,
            }
        case GameEnded():
            return "game:ended", {
                "gameId": game_id,
                "reason": event.reason.value,
                "winner": event.winner,
                "scores": list(event.scores),
                "cats": [[x, y] for x, y in event.cats],
                "version": event.version,
            }
    raise TypeError(f"알 수 없는 이벤트입니다: {event!r}")
