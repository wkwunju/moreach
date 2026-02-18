"""Add custom prompt columns to reddit_campaigns table

Revision ID: 0007
Revises: 0006
Create Date: 2026-02-18

Allows per-campaign custom prompts for comment and DM generation.

IMPORTANT: All DDL is fully idempotent using SQL-level checks (DO/EXCEPTION)
to handle concurrent execution from multiple Railway instances.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0007'
down_revision: Union[str, None] = '0006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    conn.execute(sa.text("""
        DO $$ BEGIN
            ALTER TABLE reddit_campaigns ADD COLUMN custom_comment_prompt TEXT DEFAULT '';
        EXCEPTION
            WHEN duplicate_column THEN null;
        END $$;
    """))

    conn.execute(sa.text("""
        DO $$ BEGIN
            ALTER TABLE reddit_campaigns ADD COLUMN custom_dm_prompt TEXT DEFAULT '';
        EXCEPTION
            WHEN duplicate_column THEN null;
        END $$;
    """))


def downgrade() -> None:
    op.drop_column('reddit_campaigns', 'custom_dm_prompt')
    op.drop_column('reddit_campaigns', 'custom_comment_prompt')
