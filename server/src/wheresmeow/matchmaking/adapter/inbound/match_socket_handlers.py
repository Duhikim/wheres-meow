from collections.abc import Callable

from flask_socketio import SocketIO

from wheresmeow.matchmaking.application.port.inbound import JoinMatchUseCase, LeaveMatchUseCase


def register_match_socket_handlers(
    socketio: SocketIO, join: JoinMatchUseCase, leave: LeaveMatchUseCase, current_player_id: Callable[[], str]
) -> None:
    @socketio.on("match:join")
    def on_join(*_args):
        join.join_match(current_player_id())  # match:waiting 은 MatchNotifier 가 보낸다

    @socketio.on("match:leave")
    def on_leave(*_args):
        leave.leave_match(current_player_id())
