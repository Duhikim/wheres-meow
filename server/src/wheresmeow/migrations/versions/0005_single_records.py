"""single_records 테이블 생성 (혼자 연습 최고 기록)

Revision ID: 0005
"""

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "single_records",
        sa.Column("player_id", sa.String(64), primary_key=True),
        sa.Column("difficulty", sa.String(16), primary_key=True),
        sa.Column("best_ms", sa.Integer(), nullable=False),
        sa.Column("clears", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("single_records")
