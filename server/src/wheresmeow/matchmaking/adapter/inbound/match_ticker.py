import logging
from collections.abc import Callable

from flask_socketio import SocketIO

logger = logging.getLogger(__name__)

TICK_SECONDS = 1.0

Repeater = Callable[[Callable[[], None]], None]
"""작업을 받아 주기적으로 실행하기 시작한다. 테스트는 직접 tick 하는 가짜를 넘긴다."""


def socketio_repeater(socketio: SocketIO, interval_s: float = TICK_SECONDS) -> Repeater:
    """Socket.IO 백그라운드 작업으로 interval_s 마다 작업을 실행한다(threading 이면 스레드, gevent 이면 greenlet)."""

    def start(task: Callable[[], None]) -> None:
        def loop() -> None:
            while True:
                socketio.sleep(interval_s)
                try:
                    task()
                except Exception:
                    logger.exception("매칭 틱 실패")  # 남기고 다음 틱은 계속한다

        socketio.start_background_task(loop)

    return start
