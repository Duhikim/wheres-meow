"""끝난 대국 하나에 대한 재대결 협상(스펙 4.1). 규칙만 판정하고, 알림·새 대국 생성은 서비스가 한다."""

from enum import StrEnum

from wheresmeow.game.domain.errors import NotAParticipant, RematchExpired

REMATCH_WINDOW_MS = 30_000


class RematchClosed(StrEnum):
    STARTED = "STARTED"
    DECLINED = "DECLINED"
    EXPIRED = "EXPIRED"
    LEFT = "LEFT"
    UNAVAILABLE = "UNAVAILABLE"  # 새 대국을 만들 수 없었다(그 사이 다른 대국에 들어간 경우 등)


class Rematch:
    def __init__(self, game_id: str, players: tuple[str, str], bot_player_id: str | None = None) -> None:
        self.game_id = game_id
        self.players = players
        self.bot_player_id = bot_player_id
        self.requested: set[str] = set()
        self.deadline_ms: int | None = None  # 첫 요청 뒤 30초
        self.closed: RematchClosed | None = None

    def request(self, player_id: str, now_ms: int) -> bool:
        """요청(또는 수락)한다. 두 사람이 모두 요청한 상태가 되면 True: 새 대국을 시작해야 한다."""
        self._require_participant(player_id)
        if self.closed is None and self.deadline_ms is not None and now_ms >= self.deadline_ms:
            self.closed = RematchClosed.EXPIRED
        if self.closed is not None:
            raise RematchExpired(f"재대결 신청이 끝났습니다({self.closed.value}): {self.game_id}")
        if self.deadline_ms is None:
            self.deadline_ms = now_ms + REMATCH_WINDOW_MS
        self.requested.add(player_id)
        if self.bot_player_id is not None:
            self.requested.add(self.bot_player_id)  # 봇은 즉시 수락한다
        if self.requested == set(self.players):
            self.closed = RematchClosed.STARTED
            return True
        return False

    def decline(self, player_id: str) -> list[str]:
        """닫고, 알려야 할 사람(이미 요청한 상대)을 돌려준다."""
        self._require_participant(player_id)
        return self._close(RematchClosed.DECLINED, notify=[p for p in self.requested if p != player_id])

    def leave(self, player_id: str) -> list[str]:
        """결과 화면을 떠났다. 닫고 상대에게 알린다(상대의 재대결 버튼을 끄도록)."""
        self._require_participant(player_id)
        return self._close(RematchClosed.LEFT, notify=[self.opponent_of(player_id)])

    def expire(self, now_ms: int) -> list[str]:
        """마감이 지난 열린 요청을 닫고 두 사람에게 알린다."""
        if self.closed is not None or self.deadline_ms is None or now_ms < self.deadline_ms:
            return []
        return self._close(RematchClosed.EXPIRED, notify=list(self.players))

    def fail(self) -> list[str]:
        """새 대국을 만들지 못했다. 두 사람에게 알린다."""
        self.closed = RematchClosed.UNAVAILABLE
        return list(self.players)

    def opponent_of(self, player_id: str) -> str:
        return self.players[1] if self.players[0] == player_id else self.players[0]

    def _close(self, reason: RematchClosed, notify: list[str]) -> list[str]:
        if self.closed is not None:
            return []
        self.closed = reason
        return [p for p in notify if p != self.bot_player_id]

    def _require_participant(self, player_id: str) -> None:
        if player_id not in self.players:
            raise NotAParticipant(f"대국 참가자가 아닙니다: {player_id}")
