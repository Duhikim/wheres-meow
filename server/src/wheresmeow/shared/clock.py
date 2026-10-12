"""현재 시각을 밀리초 epoch 로 제공하는 포트와 구현."""

import time
from typing import Protocol


class Clock(Protocol):
    def now_ms(self) -> int: ...


class SystemClock:
    def now_ms(self) -> int:
        return int(time.time() * 1000)
