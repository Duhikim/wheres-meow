from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from wheresmeow.shared.persistence.database import Base


class PlayerRow(Base):
    """회원과 게스트 모두의 공통 신원(스펙 6절 players)."""

    __tablename__ = "players"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    kind: Mapped[str] = mapped_column(String(10))
    nickname: Mapped[str] = mapped_column(String(12))
    skin_1p: Mapped[int] = mapped_column(Integer)
    skin_2p: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
