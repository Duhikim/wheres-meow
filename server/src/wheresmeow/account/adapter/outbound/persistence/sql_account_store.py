from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from wheresmeow.account.adapter.outbound.persistence.models import AccountRow, OAuthIdentityRow, PlayerRow
from wheresmeow.account.application.port.outbound import Credential
from wheresmeow.account.domain.member import NicknameTaken, UsernameTaken
from wheresmeow.account.domain.player import Player, PlayerKind
from wheresmeow.shared.clock import Clock
from wheresmeow.shared.persistence.database import Database, ms_to_datetime


class SqlAccountStore:
    """AccountStore 포트의 DB 구현. 플레이어 행과 계정 행을 한 트랜잭션으로 만든다."""

    def __init__(self, database: Database, clock: Clock) -> None:
        self._database = database
        self._clock = clock

    def create_member(self, player: Player, username: str | None, password_hash: str | None) -> None:
        try:
            with self._database.session() as session:
                session.add(self._player_row(player))
                session.flush()  # 플레이어를 먼저 넣어야 계정의 외래 키가 맞는다
                session.add(AccountRow(player_id=player.id, username=username, password_hash=password_hash))
        except IntegrityError as error:
            # 동시에 같은 아이디·닉네임으로 가입하면 서비스 검사를 지나 DB 제약에서 걸린다
            if username is not None and self.username_taken(username):
                raise UsernameTaken("이미 쓰는 아이디입니다") from error
            raise NicknameTaken("이미 쓰는 닉네임입니다") from error

    def create_oauth_member(self, player: Player, provider: str, provider_user_id: str) -> None:
        try:
            with self._database.session() as session:
                session.add(self._player_row(player))
                session.flush()
                session.add(AccountRow(player_id=player.id, username=None, password_hash=None))
                session.add(OAuthIdentityRow(provider=provider, provider_user_id=provider_user_id, player_id=player.id))
        except IntegrityError as error:
            raise NicknameTaken("임시 닉네임이 겹쳤습니다. 다시 시도해 주세요") from error

    def find_credential(self, username: str) -> Credential | None:
        with self._database.session() as session:
            row = session.scalars(select(AccountRow).where(AccountRow.username == username)).first()
            return None if row is None else Credential(row.player_id, row.password_hash)

    def username_taken(self, username: str) -> bool:
        return self.find_credential(username) is not None

    def member_nickname_taken(self, nickname: str, except_player_id: str | None = None) -> bool:
        with self._database.session() as session:
            query = select(PlayerRow.id).where(
                PlayerRow.kind == PlayerKind.MEMBER.value, PlayerRow.nickname == nickname
            )
            if except_player_id is not None:
                query = query.where(PlayerRow.id != except_player_id)
            return session.scalars(query).first() is not None

    def find_player_by_oauth(self, provider: str, provider_user_id: str) -> str | None:
        with self._database.session() as session:
            row = session.get(OAuthIdentityRow, (provider, provider_user_id))
            return None if row is None else row.player_id

    def _player_row(self, player: Player) -> PlayerRow:
        now = ms_to_datetime(self._clock.now_ms())
        return PlayerRow(
            id=player.id,
            kind=player.kind.value,
            nickname=player.nickname,
            skin_1p=player.skin_1p,
            skin_2p=player.skin_2p,
            needs_nickname=player.needs_nickname,
            created_at=now,
            last_seen_at=now,
        )
