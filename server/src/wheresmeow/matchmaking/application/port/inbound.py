"""matchmaking 도메인이 바깥에 제공하는 유스케이스."""

from typing import Protocol


class JoinMatchUseCase(Protocol):
    def join_match(self, player_id: str) -> None:
        """대기열에 들어간다. 이미 대기 중이면 ALREADY_QUEUED, 대국 중이면 ALREADY_IN_GAME."""
        ...


class LeaveMatchUseCase(Protocol):
    def leave_match(self, player_id: str) -> None:
        """대기열에서 나온다. 대기 중이 아니면 아무것도 하지 않는다(연결 끊김에서도 부른다)."""
        ...
