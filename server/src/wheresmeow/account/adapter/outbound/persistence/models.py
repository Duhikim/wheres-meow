from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, false, text
from sqlalchemy.orm import Mapped, mapped_column

from wheresmeow.shared.persistence.database import Base

MEMBER_ONLY = text("kind = 'MEMBER'")


class PlayerRow(Base):
    """회원과 게스트 모두의 공통 신원(스펙 6절 players)."""

    __tablename__ = "players"
    __table_args__ = (
        # 회원 닉네임은 서비스 전체에서 유일하다. 게스트는 겹쳐도 된다(스펙 4.4·6절).
        Index(
            "uq_players_member_nickname",
            "nickname",
            unique=True,
            postgresql_where=MEMBER_ONLY,
            sqlite_where=MEMBER_ONLY,
        ),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    kind: Mapped[str] = mapped_column(String(10))
    nickname: Mapped[str] = mapped_column(String(12))
    skin_1p: Mapped[int] = mapped_column(Integer)
    skin_2p: Mapped[int] = mapped_column(Integer)
    needs_nickname: Mapped[bool] = mapped_column(Boolean, server_default=false())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class AccountRow(Base):
    """회원의 로그인 정보. 소셜 로그인만 쓰는 회원은 username·password_hash 가 비어 있다."""

    __tablename__ = "accounts"

    player_id: Mapped[str] = mapped_column(String(64), ForeignKey("players.id"), primary_key=True)
    username: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)


class OAuthIdentityRow(Base):
    __tablename__ = "oauth_identities"

    provider: Mapped[str] = mapped_column(String(20), primary_key=True)
    provider_user_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    player_id: Mapped[str] = mapped_column(String(64), ForeignKey("players.id"), index=True)


class RefreshTokenRow(Base):
    """리프레시 토큰은 해시만 저장한다(스펙 4.4)."""

    __tablename__ = "refresh_tokens"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    player_id: Mapped[str] = mapped_column(String(64), ForeignKey("players.id"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
