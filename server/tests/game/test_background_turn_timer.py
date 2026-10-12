import logging
import threading

from flask import Flask
from flask_socketio import SocketIO

from wheresmeow.game.adapter.outbound.timer.background_turn_timer import BackgroundTurnTimer
from wheresmeow.shared.clock import SystemClock


def make_timer() -> tuple[BackgroundTurnTimer, SystemClock]:
    clock = SystemClock()
    return BackgroundTurnTimer(SocketIO(Flask(__name__), async_mode="threading"), clock), clock


class TestBackgroundTurnTimer:
    class TestSchedule:
        def test_성공_마감_시각이_지나면_콜백을_부른다(self):
            timer, clock = make_timer()
            fired = threading.Event()
            calls = []

            def on_expire(game_id, turn_seq):
                calls.append((game_id, turn_seq))
                fired.set()

            timer.schedule("g1", 3, clock.now_ms() + 30, on_expire)

            assert fired.wait(timeout=2)
            assert calls == [("g1", 3)]

        def test_성공_콜백_예외는_로그로_남기고_삼키지_않는다(self, caplog):
            timer, clock = make_timer()
            done = threading.Event()

            def on_expire(game_id, turn_seq):
                done.set()
                raise RuntimeError("boom")

            with caplog.at_level(logging.ERROR):
                timer.schedule("g1", 1, clock.now_ms(), on_expire)
                assert done.wait(timeout=2)
                for _ in range(50):
                    if "턴 만료 처리 실패" in caplog.text:
                        break
                    threading.Event().wait(0.02)

            assert "턴 만료 처리 실패" in caplog.text
