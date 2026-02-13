"""Add last_login_at to users table

Revision ID: 0005
Revises: 0004
Create Date: 2026-02-13

Tracks user last login time for retention analysis in admin dashboard.

IMPORTANT: All DDL is fully idempotent using SQL-level checks (DO/EXCEPTION)
to handle concurrent execution from multiple Railway instances.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0005'
down_revision: Union[str, None] = '0004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    conn.execute(sa.text("""
        DO $$ BEGIN
            ALTER TABLE users ADD COLUMN last_login_at TIMESTAMP;
        EXCEPTION
            WHEN duplicate_column THEN null;
        END $$;
    """))


def downgrade() -> None:
    op.drop_column('users', 'last_login_at')
