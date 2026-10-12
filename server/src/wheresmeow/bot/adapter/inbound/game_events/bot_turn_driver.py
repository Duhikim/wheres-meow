"""봇 차례 진행기. game 의 GameEventPublisher 포트를 구현해 대국 이벤트를 받고, 봇 차례면 수를 둔다."""

import logging
import random
from collections.abc import Callable, Sequence

from wheresmeow.bot.domain.solver import BoardView, Difficulty, choose_cell
from wheresmeow.game.application.port.inbound import GetGameUseCase, RevealCellUseCase
from wheresmeow.game.domain.game import Game, GameEvent, GameMode, GameStatus
from wheresmeow.shared.errors import DomainError

logger = logging.getLogger(__name__)

Scheduler = Callable[[Callable[[], None]], None]


def to_view(game: Game) -> BoardView:
    """판에서 사람에게 보이는 정보만 꺼낸다. 고양이 배치(board.cats)는 남은 수 외에는 넘기지 않는다."""
    numbers = {(c.x, c.y): c.number for c in game.opened.values() if c.found_by is None}
    found = frozenset((c.x, c.y) for c in game.opened.values() if c.found_by is not None)
    remaining = len(game.board.cats) - len(found)  # 전체 고양이 수(25)는 공개 정보다
    return BoardView(size=game.board.size, numbers=numbers, found=found, remaining=remaining)  # type: ignore[arg-type]


class BotTurnDriver:
    def __init__(self, scheduler: Scheduler, rng: random.Random | None = None) -> None:
        """scheduler 는 '생각하는 시간' 뒤에 작업을 실행한다(운영: Socket.IO 백그라운드 작업)."""
        self._scheduler = scheduler
        self._rng = rng or random.Random()
        self._get_game: GetGameUseCase | None = None
        self._reveal: RevealCellUseCase | None = None

    def attach(self, *, get_game: GetGameUseCase, reveal: RevealCellUseCase) -> None:
        """GameService 와 서로를 참조하므로 생성 뒤에 연결한다."""
        self._get_game = get_game
        self._reveal = reveal

    def game_started(self, game: Game) -> None:
        self._maybe_move(game)

    def publish(self, game: Game, events: Sequence[GameEvent]) -> None:
        self._maybe_move(game)

    def _maybe_move(self, game: Game) -> None:
        if game.mode is not GameMode.BOT or game.status is not GameStatus.IN_PROGRESS:
            return
        seat = game.seats[game.current_seat]
        if not seat.is_bot:
            return
        if self._get_game is None or self._reveal is None:
            raise RuntimeError("BotTurnDriver.attach() 를 먼저 호출해야 합니다")
        assert game.bot_difficulty is not None
        game_id, bot_id, turn_seq = game.id, seat.player_id, game.turn_seq
        difficulty = Difficulty(game.bot_difficulty)
        self._scheduler(lambda: self._move(game_id, bot_id, turn_seq, difficulty))

    def _move(self, game_id: str, bot_id: str, turn_seq: int, difficulty: Difficulty) -> None:
        assert self._get_game is not None and self._reveal is not None
        try:
            game = self._get_game.get_game(game_id, bot_id)
            if game.status is not GameStatus.IN_PROGRESS or game.turn_seq != turn_seq:
                return  # 생각하는 사이 대국이 끝났거나 차례가 바뀌었다
            x, y = choose_cell(to_view(game), difficulty, self._rng)
            self._reveal.reveal(game_id, bot_id, x, y)
        except DomainError as error:
            logger.info("봇 수 취소 game_id=%s 사유=%s", game_id, error.code)  # 기권 직후 등 경쟁 상황
        except Exception:
            logger.exception("봇 수 두기 실패 game_id=%s", game_id)


def socketio_scheduler(socketio, rng: random.Random | None = None, min_s: float = 0.8, max_s: float = 2.0) -> Scheduler:
    """0.8~2초 '생각하는 시간' 뒤에 실행한다(스펙 4.6). 대국 잠금 밖의 별도 작업에서 돈다."""
    rng = rng or random.Random()

    def schedule(task: Callable[[], None]) -> None:
        def run() -> None:
            socketio.sleep(rng.uniform(min_s, max_s))
            task()

        socketio.start_background_task(run)

    return schedule
