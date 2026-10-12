"""요청을 보낸 플레이어를 알아내는 방법. HTTP 는 Bearer 토큰, 소켓은 연결 시 등록한 sid."""

import threading

from flask import request

from wheresmeow.account.application.port.inbound import AuthenticateUseCase
from wheresmeow.account.domain.player import Player
from wheresmeow.shared.errors import Unauthorized


class HttpIdentity:
    def __init__(self, authenticate: AuthenticateUseCase) -> None:
        self._authenticate = authenticate

    def current_player(self) -> Player:
        header = request.headers.get("Authorization", "")
        scheme, _, token = header.partition(" ")
        if scheme != "Bearer" or not token:
            raise Unauthorized("Authorization: Bearer <토큰> 헤더가 필요합니다")
        return self._authenticate.authenticate(token)

    def current_player_id(self) -> str:
        return self.current_player().id


class SocketSessions:
    def __init__(self) -> None:
        self._players: dict[str, str] = {}
        self._guard = threading.Lock()

    def bind(self, sid: str, player_id: str) -> None:
        with self._guard:
            self._players[sid] = player_id

    def unbind(self, sid: str) -> None:
        with self._guard:
            self._players.pop(sid, None)

    def current_player_id(self) -> str:
        with self._guard:
            player_id = self._players.get(request.sid)
        if player_id is None:
            raise Unauthorized("인증되지 않은 소켓 연결입니다")
        return player_id
