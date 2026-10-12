import logging
from collections.abc import Callable

from flask_socketio import SocketIO

from wheresmeow.shared.clock import Clock

logger = logging.getLogger(__name__)


class BackgroundTurnTimer:
    """Socket.IO 의 백그라운드 작업으로 턴 마감을 기다린다.

    async_mode 가 threading 이면 스레드, gevent 이면 greenlet 으로 동작한다.
    취소 기능은 없다. 지나간 턴의 만료는 Game.timeout 이 turn_seq 로 걸러 낸다.
    """

    def __init__(self, socketio: SocketIO, clock: Clock) -> None:
        self._socketio = socketio
        self._clock = clock

    def schedule(
        self,
        game_id: str,
        turn_seq: int,
        deadline_ms: int,
        on_expire: Callable[[str, int], None],
    ) -> None:
        self._socketio.start_background_task(self._run, game_id, turn_seq, deadline_ms, on_expire)

    def _run(self, game_id: str, turn_seq: int, deadline_ms: int, on_expire: Callable[[str, int], None]) -> None:
        self._socketio.sleep(max(0, deadline_ms - self._clock.now_ms()) / 1000)
        try:
            on_expire(game_id, turn_seq)
        except Exception:
            logger.exception("턴 만료 처리 실패 game_id=%s turn_seq=%s", game_id, turn_seq)
