"""Add poll_jobs table and poll_job_id to reddit_leads

Revision ID: 0004
Revises: 0003
Create Date: 2026-02-08

Tracks each poll run with stats, linking leads to the specific job that discovered them.
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

    # Create PollJobStatus enum (use DO/EXCEPTION to handle concurrent creation)
    # PostgreSQL enums are NOT rolled back on transaction failure, so checkfirst
    # and IF NOT EXISTS don't work reliably with connection poolers like PgBouncer.
    conn.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE polljobstatus AS ENUM ('RUNNING', 'COMPLETED', 'FAILED', 'PARTIAL');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """))

    # Create poll_jobs table if it doesn't exist
    result = conn.execute(sa.text(
        "SELECT EXISTS(SELECT 1 FROM information_schema.tables "
        "WHERE table_name = 'poll_jobs')"
    ))
    if not result.scalar():
        op.create_table('poll_jobs',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('campaign_id', sa.Integer(), nullable=False),
            sa.Column('status', sa.Enum('RUNNING', 'COMPLETED', 'FAILED', 'PARTIAL',
                                        name='polljobstatus', create_type=False), nullable=False),
            sa.Column('trigger', sa.String(32), server_default='manual', nullable=False),
            sa.Column('subreddits_polled', sa.Integer(), server_default='0', nullable=False),
            sa.Column('posts_fetched', sa.Integer(), server_default='0', nullable=False),
            sa.Column('posts_scored', sa.Integer(), server_default='0', nullable=False),
            sa.Column('leads_created', sa.Integer(), server_default='0', nullable=False),
            sa.Column('leads_deleted', sa.Integer(), server_default='0', nullable=False),
            sa.Column('suggestions_generated', sa.Integer(), server_default='0', nullable=False),
            sa.Column('error_message', sa.Text(), server_default='', nullable=False),
            sa.Column('started_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['campaign_id'], ['reddit_campaigns.id']),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_poll_jobs_campaign_id', 'poll_jobs', ['campaign_id'])

    # Add poll_job_id to reddit_leads (nullable for existing data)
    result = conn.execute(sa.text(
        "SELECT EXISTS(SELECT 1 FROM information_schema.columns "
        "WHERE table_name = 'reddit_leads' AND column_name = 'poll_job_id')"
    ))
    if not result.scalar():
        op.add_column('reddit_leads',
            sa.Column('poll_job_id', sa.Integer(), nullable=True))
        op.create_foreign_key(
            'fk_reddit_leads_poll_job_id',
            'reddit_leads', 'poll_jobs',
            ['poll_job_id'], ['id']
        )
        op.create_index('ix_reddit_leads_poll_job_id', 'reddit_leads', ['poll_job_id'])


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
