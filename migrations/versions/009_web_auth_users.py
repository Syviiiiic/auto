"""web auth: email, password_hash, nullable telegram_id

Revision ID: 009_web_auth
Revises: 008_add_notifications
Create Date: 2026-03-29

"""
from alembic import op
import sqlalchemy as sa

revision = "009_web_auth"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("email", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("password_hash", sa.String(255), nullable=True))
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.alter_column("users", "telegram_id", existing_type=sa.BigInteger(), nullable=True)


def downgrade() -> None:
    op.alter_column("users", "telegram_id", existing_type=sa.BigInteger(), nullable=False)
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_column("users", "password_hash")
    op.drop_column("users", "email")
