from typing import Protocol

from wheresmeow.account.domain.player import Player


class PlayerStore(Protocol):
    def save(self, player: Player) -> None: ...

    def get(self, player_id: str) -> Player | None: ...


class TokenIssuer(Protocol):
    def issue(self, player_id: str) -> str: ...

    def verify(self, token: str) -> str:
        """player_id 를 돌려준다. 위조·만료면 Unauthorized."""
        ...
