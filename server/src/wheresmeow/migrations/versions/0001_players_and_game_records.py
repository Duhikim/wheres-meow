"""players, game_records 테이블 생성 (2단계 저장·재접속)

Revision ID: 0001
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "players",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("kind", sa.String(10), nullable=False),
        sa.Column("nickname", sa.String(12), nullable=False),
        sa.Column("skin_1p", sa.Integer(), nullable=False),
        sa.Column("skin_2p", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "game_records",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("mode", sa.String(10), nullable=False),
        sa.Column("bot_difficulty", sa.String(10), nullable=True),
        sa.Column("seat0_player_id", sa.String(64), nullable=False),
        sa.Column("seat0_nickname", sa.String(12), nullable=False),
        sa.Column("seat0_skin", sa.Integer(), nullable=False),
        sa.Column("seat0_score", sa.Integer(), nullable=False),
        sa.Column("seat1_player_id", sa.String(64), nullable=False),
        sa.Column("seat1_nickname", sa.String(12), nullable=False),
        sa.Column("seat1_skin", sa.Integer(), nullable=False),
        sa.Column("seat1_score", sa.Integer(), nullable=False),
        sa.Column("winner_seat", sa.Integer(), nullable=True),
        sa.Column("end_reason", sa.String(20), nullable=False),
        sa.Column("cats", sa.JSON(), nullable=False),
        sa.Column("moves", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_game_records_seat0_player_id", "game_records", ["seat0_player_id"])
    op.create_index("ix_game_records_seat1_player_id", "game_records", ["seat1_player_id"])
    op.create_index("ix_game_records_ended_at", "game_records", ["ended_at"])


def downgrade() -> None:
    op.drop_table("game_records")
    op.drop_table("players")
