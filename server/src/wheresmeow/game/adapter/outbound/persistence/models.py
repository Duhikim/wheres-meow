from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from wheresmeow.shared.persistence.database import Base


class GameRecordRow(Base):
    """끝난 대국 기록(스펙 6절 game_records). 수순은 다시보기·분쟁 확인용으로 남긴다."""

    __tablename__ = "game_records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    mode: Mapped[str] = mapped_column(String(10))
    bot_difficulty: Mapped[str | None] = mapped_column(String(10), nullable=True)
    seat0_player_id: Mapped[str] = mapped_column(String(64), index=True)
    seat0_nickname: Mapped[str] = mapped_column(String(12))
    seat0_skin: Mapped[int] = mapped_column(Integer)
    seat0_score: Mapped[int] = mapped_column(Integer)
    seat1_player_id: Mapped[str] = mapped_column(String(64), index=True)
    seat1_nickname: Mapped[str] = mapped_column(String(12))
    seat1_skin: Mapped[int] = mapped_column(Integer)
    seat1_score: Mapped[int] = mapped_column(Integer)
    winner_seat: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 무승부면 None
    end_reason: Mapped[str] = mapped_column(String(20))
    cats: Mapped[list] = mapped_column(JSON)
    moves: Mapped[list] = mapped_column(JSON)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
