from collections.abc import Sequence

from flask_socketio import SocketIO

from wheresmeow.game.adapter.outbound.socket.payloads import event_payload, started_payload
from wheresmeow.game.domain.game import Game, GameEvent
from wheresmeow.shared.socket_rooms import player_room


class SocketIOGameEventPublisher:
    """두 참가자의 player 룸으로 이벤트를 보낸다."""

    def __init__(self, socketio: SocketIO) -> None:
        self._socketio = socketio

    def game_started(self, game: Game) -> None:
        for index, seat in enumerate(game.seats):
            self._socketio.emit("game:started", started_payload(game, index), to=player_room(seat.player_id))

    def publish(self, game: Game, events: Sequence[GameEvent]) -> None:
        for event in events:
            name, payload = event_payload(game.id, event)
            for seat in game.seats:
                self._socketio.emit(name, payload, to=player_room(seat.player_id))
