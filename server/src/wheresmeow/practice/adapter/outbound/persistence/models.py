from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from wheresmeow.shared.persistence.database import Base


class SingleRecordRow(Base):
    """혼자 연습 최고 기록. 난이도별로 가장 빠른 클리어 시간과 클리어 횟수만 남긴다(전적은 세지 않는다)."""

    __tablename__ = "single_records"

    player_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    difficulty: Mapped[str] = mapped_column(String(16), primary_key=True)
    best_ms: Mapped[int] = mapped_column(Integer)
    clears: Mapped[int] = mapped_column(Integer)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
