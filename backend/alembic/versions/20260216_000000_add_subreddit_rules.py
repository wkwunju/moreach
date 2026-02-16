"""Add rules_json and rules_summary to subreddit_cache table

Revision ID: 0006
Revises: 0005
Create Date: 2026-02-16

Stores subreddit rules fetched from Reddit API and LLM-generated summaries.

IMPORTANT: All DDL is fully idempotent using SQL-level checks (DO/EXCEPTION)
to handle concurrent execution from multiple Railway instances.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0006'
down_revision: Union[str, None] = '0005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    conn.execute(sa.text("""
        DO $$ BEGIN
            ALTER TABLE subreddit_cache ADD COLUMN rules_json TEXT DEFAULT '';
        EXCEPTION
            WHEN duplicate_column THEN null;
        END $$;
    """))

    conn.execute(sa.text("""
        DO $$ BEGIN
            ALTER TABLE subreddit_cache ADD COLUMN rules_summary TEXT DEFAULT '';
        EXCEPTION
            WHEN duplicate_column THEN null;
        END $$;
    """))


def downgrade() -> None:
    op.drop_column('subreddit_cache', 'rules_summary')
    op.drop_column('subreddit_cache', 'rules_json')
