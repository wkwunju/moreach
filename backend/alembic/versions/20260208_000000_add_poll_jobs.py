"""Add poll_jobs table and poll_job_id to reddit_leads

Revision ID: 0004
Revises: 0003
Create Date: 2026-02-08

Tracks each poll run with stats, linking leads to the specific job that discovered them.

IMPORTANT: All DDL is fully idempotent using SQL-level checks (IF NOT EXISTS,
DO/EXCEPTION) to handle concurrent execution from multiple Railway instances.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0004'
down_revision: Union[str, None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Create enum type (idempotent via EXCEPTION handler)
    conn.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE polljobstatus AS ENUM ('RUNNING', 'COMPLETED', 'FAILED', 'PARTIAL');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """))

    # 2. Create poll_jobs table (idempotent via IF NOT EXISTS)
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS poll_jobs (
            id SERIAL PRIMARY KEY,
            campaign_id INTEGER NOT NULL REFERENCES reddit_campaigns(id),
            status polljobstatus NOT NULL,
            trigger VARCHAR(32) NOT NULL DEFAULT 'manual',
            subreddits_polled INTEGER NOT NULL DEFAULT 0,
            posts_fetched INTEGER NOT NULL DEFAULT 0,
            posts_scored INTEGER NOT NULL DEFAULT 0,
            leads_created INTEGER NOT NULL DEFAULT 0,
            leads_deleted INTEGER NOT NULL DEFAULT 0,
            suggestions_generated INTEGER NOT NULL DEFAULT 0,
            error_message TEXT NOT NULL DEFAULT '',
            started_at TIMESTAMP NOT NULL DEFAULT now(),
            completed_at TIMESTAMP
        );
    """))

    # 3. Create index on poll_jobs (idempotent via IF NOT EXISTS)
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_poll_jobs_campaign_id ON poll_jobs (campaign_id);
    """))

    # 4. Add poll_job_id column to reddit_leads (idempotent via EXCEPTION handler)
    conn.execute(sa.text("""
        DO $$ BEGIN
            ALTER TABLE reddit_leads ADD COLUMN poll_job_id INTEGER;
        EXCEPTION
            WHEN duplicate_column THEN null;
        END $$;
    """))

    # 5. Add foreign key constraint (idempotent via EXCEPTION handler)
    conn.execute(sa.text("""
        DO $$ BEGIN
            ALTER TABLE reddit_leads
                ADD CONSTRAINT fk_reddit_leads_poll_job_id
                FOREIGN KEY (poll_job_id) REFERENCES poll_jobs(id);
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """))

    # 6. Create index on reddit_leads.poll_job_id (idempotent via IF NOT EXISTS)
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_reddit_leads_poll_job_id ON reddit_leads (poll_job_id);
    """))


def downgrade() -> None:
    op.drop_index('ix_reddit_leads_poll_job_id', table_name='reddit_leads')
    op.drop_constraint('fk_reddit_leads_poll_job_id', 'reddit_leads', type_='foreignkey')
    op.drop_column('reddit_leads', 'poll_job_id')
    op.drop_index('ix_poll_jobs_campaign_id', table_name='poll_jobs')
    op.drop_table('poll_jobs')

    conn = op.get_bind()
    conn.execute(sa.text("""
        DO $$ BEGIN
            DROP TYPE polljobstatus;
        EXCEPTION
            WHEN undefined_object THEN null;
        END $$;
    """))
