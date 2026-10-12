from collections.abc import Sequence

from wheresmeow.game.application.port.outbound import GameEventPublisher
from wheresmeow.game.domain.game import Game, GameEvent


class CompositeGameEventPublisher:
    """여러 발행기에 차례로 전달한다(소켓 알림, 봇 차례 진행기 등). 순서가 곧 전달 순서다."""

    def __init__(self, publishers: Sequence[GameEventPublisher]) -> None:
        self._publishers = list(publishers)

    def game_started(self, game: Game) -> None:
        for publisher in self._publishers:
            publisher.game_started(game)

    def publish(self, game: Game, events: Sequence[GameEvent]) -> None:
        for publisher in self._publishers:
            publisher.publish(game, events)
