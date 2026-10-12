"""bot_records 테이블 생성 (4단계 컴퓨터 대전)

Revision ID: 0002
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "bot_records",
        sa.Column("player_id", sa.String(64), primary_key=True),
        sa.Column("difficulty", sa.String(10), primary_key=True),
        sa.Column("wins", sa.Integer(), nullable=False),
        sa.Column("losses", sa.Integer(), nullable=False),
        sa.Column("draws", sa.Integer(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("bot_records")
