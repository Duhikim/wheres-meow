"""회원 계정: accounts·oauth_identities·refresh_tokens, players.needs_nickname, 회원 닉네임 부분 유일 인덱스 (5단계)

Revision ID: 0003
"""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

MEMBER_ONLY = sa.text("kind = 'MEMBER'")


def upgrade() -> None:
    with op.batch_alter_table("players") as batch:
        batch.add_column(sa.Column("needs_nickname", sa.Boolean(), server_default=sa.false(), nullable=False))
    op.create_index(
        "uq_players_member_nickname",
        "players",
        ["nickname"],
        unique=True,
        postgresql_where=MEMBER_ONLY,
        sqlite_where=MEMBER_ONLY,
    )
    op.create_table(
        "accounts",
        sa.Column("player_id", sa.String(64), sa.ForeignKey("players.id"), primary_key=True),
        sa.Column("username", sa.String(20), nullable=True, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=True),
    )
    op.create_table(
        "oauth_identities",
        sa.Column("provider", sa.String(20), primary_key=True),
        sa.Column("provider_user_id", sa.String(128), primary_key=True),
        sa.Column("player_id", sa.String(64), sa.ForeignKey("players.id"), nullable=False),
    )
    op.create_index("ix_oauth_identities_player_id", "oauth_identities", ["player_id"])
    op.create_table(
        "refresh_tokens",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column("player_id", sa.String(64), sa.ForeignKey("players.id"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_refresh_tokens_player_id", "refresh_tokens", ["player_id"])


def downgrade() -> None:
    op.drop_table("refresh_tokens")
    op.drop_table("oauth_identities")
    op.drop_table("accounts")
    op.drop_index("uq_players_member_nickname", table_name="players")
    with op.batch_alter_table("players") as batch:
        batch.drop_column("needs_nickname")
