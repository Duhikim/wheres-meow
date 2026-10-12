from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from wheresmeow.shared.persistence.database import Base


class RatingRow(Base):
    """사람 간 대국 레이팅과 승패(스펙 6절 ratings). 첫 대국을 마칠 때 만든다. 게스트도 가진다."""

    __tablename__ = "ratings"

    player_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    rating: Mapped[int] = mapped_column(Integer, index=True)
    games: Mapped[int] = mapped_column(Integer)
    wins: Mapped[int] = mapped_column(Integer)
    losses: Mapped[int] = mapped_column(Integer)
    draws: Mapped[int] = mapped_column(Integer)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class RatingChangeRow(Base):
    """대국 하나가 한 사람의 레이팅을 어떻게 바꿨는지(스펙 6절 rating_changes)."""

    __tablename__ = "rating_changes"

    game_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    player_id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    before: Mapped[int] = mapped_column(Integer)
    after: Mapped[int] = mapped_column(Integer)
