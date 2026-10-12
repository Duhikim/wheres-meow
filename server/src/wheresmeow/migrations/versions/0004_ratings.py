"""ratings·rating_changes 테이블 생성 (6단계 레이팅)

Revision ID: 0004
"""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ratings",
        sa.Column("player_id", sa.String(64), primary_key=True),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("games", sa.Integer(), nullable=False),
        sa.Column("wins", sa.Integer(), nullable=False),
        sa.Column("losses", sa.Integer(), nullable=False),
        sa.Column("draws", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_ratings_rating", "ratings", ["rating"])
    op.create_table(
        "rating_changes",
        sa.Column("game_id", sa.String(64), primary_key=True),
        sa.Column("player_id", sa.String(64), primary_key=True),
        sa.Column("before", sa.Integer(), nullable=False),
        sa.Column("after", sa.Integer(), nullable=False),
    )
    op.create_index("ix_rating_changes_player_id", "rating_changes", ["player_id"])


def downgrade() -> None:
    op.drop_index("ix_rating_changes_player_id", table_name="rating_changes")
    op.drop_table("rating_changes")
    op.drop_index("ix_ratings_rating", table_name="ratings")
    op.drop_table("ratings")
