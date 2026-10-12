from flask_socketio import SocketIO

from wheresmeow.shared.socket_rooms import player_room


class SocketIORematchNotifier:
    """RematchNotifier 포트의 Socket.IO 구현. 알릴 사람의 player 룸으로만 보낸다."""

    def __init__(self, socketio: SocketIO) -> None:
        self._socketio = socketio

    def rematch_requested(self, game_id: str, to_player_id: str) -> None:
        self._socketio.emit("game:rematch-requested", {"gameId": game_id}, to=player_room(to_player_id))

    def rematch_cancelled(self, game_id: str, to_player_ids: list[str], reason: str) -> None:
        for player_id in to_player_ids:
            self._socketio.emit(
                "game:rematch-cancelled", {"gameId": game_id, "reason": reason}, to=player_room(player_id)
            )
