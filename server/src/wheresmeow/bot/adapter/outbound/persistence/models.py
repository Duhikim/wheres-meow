from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from wheresmeow.shared.persistence.database import Base


class BotRecordRow(Base):
    """컴퓨터 대전 전적(스펙 6절 bot_records). 레이팅과 별개로 난이도별로 센다."""

    __tablename__ = "bot_records"

    player_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    difficulty: Mapped[str] = mapped_column(String(10), primary_key=True)
    wins: Mapped[int] = mapped_column(Integer, default=0)
    losses: Mapped[int] = mapped_column(Integer, default=0)
    draws: Mapped[int] = mapped_column(Integer, default=0)
