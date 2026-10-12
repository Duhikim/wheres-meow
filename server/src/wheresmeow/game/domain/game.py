"""대국 엔티티. 규칙 판정은 모두 여기서 하며 Flask·DB 를 모른다."""

from collections import deque
from dataclasses import dataclass, field
from enum import StrEnum

from wheresmeow.game.domain.board import Board, Position
from wheresmeow.game.domain.errors import (
    CellAlreadyOpen,
    GameFinished,
    NotAParticipant,
    NotYourTurn,
    OutOfBoard,
)

TURN_MS = 20_000
MAX_CONSECUTIVE_TIMEOUTS = 3


class GameMode(StrEnum):
    INVITE = "INVITE"
    MATCH = "MATCH"
    BOT = "BOT"


class GameStatus(StrEnum):
    IN_PROGRESS = "IN_PROGRESS"
    FINISHED = "FINISHED"


class EndReason(StrEnum):
    ALL_FOUND = "ALL_FOUND"
    FORFEIT = "FORFEIT"
    AUTO_FORFEIT = "AUTO_FORFEIT"


@dataclass
class Seat:
    player_id: str
    nickname: str
    skin: int
    score: int = 0
    consecutive_timeouts: int = 0


@dataclass(frozen=True)
class OpenedCell:
    x: int
    y: int
    number: int | None  # 숫자·빈 칸이면 주변 고양이 수, 고양이 칸이면 None
    found_by: int | None  # 고양이 칸이면 찾은 좌석(0 또는 1)


@dataclass(frozen=True)
class CellsRevealed:
    version: int
    seat: int
    cells: tuple[OpenedCell, ...]
    scores: tuple[int, int]
    current_seat: int
    turn_deadline_ms: int | None


@dataclass(frozen=True)
class TurnTimedOut:
    version: int
    seat: int
    scores: tuple[int, int]
    current_seat: int
    turn_deadline_ms: int | None


@dataclass(frozen=True)
class GameEnded:
    version: int
    reason: EndReason
    winner: int | None  # None 이면 무승부
    scores: tuple[int, int]
    cats: tuple[Position, ...]


GameEvent = CellsRevealed | TurnTimedOut | GameEnded


@dataclass
class Game:
    id: str
    mode: GameMode
    board: Board
    seats: tuple[Seat, Seat]
    first_seat: int
    started_at_ms: int
    bot_difficulty: str | None = None  # 컴퓨터 대전이면 EASY·NORMAL·HARD
    status: GameStatus = GameStatus.IN_PROGRESS
    version: int = 0
    turn_seq: int = 0
    current_seat: int = 0
    turn_deadline_ms: int | None = None
    end_reason: EndReason | None = None
    winner: int | None = None
    opened: dict[Position, OpenedCell] = field(default_factory=dict)
    moves: list[dict] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.first_seat not in (0, 1):
            raise ValueError(f"선공 좌석은 0 또는 1 이어야 합니다: {self.first_seat}")
        if self.seats[0].player_id == self.seats[1].player_id:
            raise ValueError("같은 플레이어가 두 좌석에 앉을 수 없습니다")
        self._start_turn(self.first_seat, self.started_at_ms)

    # ---- 조회 ----

    @property
    def scores(self) -> tuple[int, int]:
        return self.seats[0].score, self.seats[1].score

    @property
    def found_count(self) -> int:
        return sum(1 for cell in self.opened.values() if cell.found_by is not None)

    def seat_of(self, player_id: str) -> int:
        for index, seat in enumerate(self.seats):
            if seat.player_id == player_id:
                return index
        raise NotAParticipant(f"대국 참가자가 아닙니다: {player_id}")

    def is_participant(self, player_id: str) -> bool:
        return any(seat.player_id == player_id for seat in self.seats)

    # ---- 동작 ----

    def reveal(self, player_id: str, x: int, y: int, now_ms: int) -> list[GameEvent]:
        self._ensure_in_progress()
        seat = self.seat_of(player_id)
        if seat != self.current_seat:
            raise NotYourTurn()
        if not self.board.in_bounds(x, y):
            raise OutOfBoard(f"판 밖의 칸입니다: ({x}, {y})")
        if (x, y) in self.opened:
            raise CellAlreadyOpen(f"이미 열린 칸입니다: ({x}, {y})")

        mover = self.seats[seat]
        mover.consecutive_timeouts = 0
        self.moves.append({"type": "reveal", "seat": seat, "x": x, "y": y, "at": now_ms})

        if self.board.is_cat(x, y):
            cell = OpenedCell(x, y, None, seat)
            self.opened[(x, y)] = cell
            mover.score += 1
            if self.found_count == len(self.board.cats):
                self._finish(EndReason.ALL_FOUND, self._leader())
                return [self._revealed(seat, (cell,)), self._ended()]
            self._start_turn(seat, now_ms)  # 고양이를 찾으면 한 번 더
            return [self._revealed(seat, (cell,))]

        cells = self._flood_open(x, y)
        self._start_turn(1 - seat, now_ms)
        return [self._revealed(seat, cells)]

    def timeout(self, turn_seq: int, now_ms: int) -> list[GameEvent]:
        """타이머 만료. 이미 지나간 턴의 타이머면 아무것도 하지 않는다."""
        if self.status is not GameStatus.IN_PROGRESS or turn_seq != self.turn_seq:
            return []
        seat = self.current_seat
        loser = self.seats[seat]
        loser.score -= 1
        loser.consecutive_timeouts += 1
        self.moves.append({"type": "timeout", "seat": seat, "at": now_ms})

        if loser.consecutive_timeouts >= MAX_CONSECUTIVE_TIMEOUTS:
            self._finish(EndReason.AUTO_FORFEIT, 1 - seat)
            return [self._timed_out(seat), self._ended()]
        self._start_turn(1 - seat, now_ms)
        return [self._timed_out(seat)]

    def forfeit(self, player_id: str, now_ms: int) -> list[GameEvent]:
        self._ensure_in_progress()
        seat = self.seat_of(player_id)
        self.moves.append({"type": "forfeit", "seat": seat, "at": now_ms})
        self._finish(EndReason.FORFEIT, 1 - seat)
        return [self._ended()]

    # ---- 내부 ----

    def _ensure_in_progress(self) -> None:
        if self.status is not GameStatus.IN_PROGRESS:
            raise GameFinished()

    def _start_turn(self, seat: int, now_ms: int) -> None:
        self.current_seat = seat
        self.turn_seq += 1
        self.turn_deadline_ms = now_ms + TURN_MS

    def _finish(self, reason: EndReason, winner: int | None) -> None:
        self.status = GameStatus.FINISHED
        self.end_reason = reason
        self.winner = winner
        self.turn_deadline_ms = None

    def _leader(self) -> int | None:
        first, second = self.scores
        if first == second:
            return None
        return 0 if first > second else 1

    def _flood_open(self, x: int, y: int) -> tuple[OpenedCell, ...]:
        opened: list[OpenedCell] = []
        queue: deque[Position] = deque([(x, y)])
        while queue:
            position = queue.popleft()
            if position in self.opened or self.board.is_cat(*position):
                continue
            number = self.board.adjacent_count(*position)
            cell = OpenedCell(position[0], position[1], number, None)
            self.opened[position] = cell
            opened.append(cell)
            if number == 0:
                queue.extend(n for n in self.board.neighbors(*position) if n not in self.opened)
        return tuple(opened)

    def _next_version(self) -> int:
        self.version += 1
        return self.version

    def _revealed(self, seat: int, cells: tuple[OpenedCell, ...]) -> CellsRevealed:
        return CellsRevealed(
            self._next_version(), seat, cells, self.scores, self.current_seat, self.turn_deadline_ms
        )

    def _timed_out(self, seat: int) -> TurnTimedOut:
        return TurnTimedOut(
            self._next_version(), seat, self.scores, self.current_seat, self.turn_deadline_ms
        )

    def _ended(self) -> GameEnded:
        assert self.end_reason is not None
        return GameEnded(
            self._next_version(), self.end_reason, self.winner, self.scores, tuple(sorted(self.board.cats))
        )
