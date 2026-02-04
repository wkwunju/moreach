"""Add usage_tracking table for API call tracking

Revision ID: 0002
Revises: 0001
Create Date: 2026-02-04

This migration adds the usage_tracking table to track API calls per user.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0002'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create APIType enum
    api_type = sa.Enum(
        'REDDIT_APIFY', 'REDDIT_RAPIDAPI', 'LLM_GEMINI', 'LLM_OPENAI', 'EMBEDDING',
        name='apitype', create_type=False
    )
    api_type.create(op.get_bind(), checkfirst=True)

    # Create usage_tracking table
    op.create_table('usage_tracking',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('api_type', sa.Enum(
            'REDDIT_APIFY', 'REDDIT_RAPIDAPI', 'LLM_GEMINI', 'LLM_OPENAI', 'EMBEDDING',
            name='apitype'), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('call_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('input_tokens', sa.Integer(), server_default='0', nullable=False),
        sa.Column('output_tokens', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'api_type', 'date', name='uq_user_api_date')
    )
    op.create_index('ix_usage_tracking_user_id', 'usage_tracking', ['user_id'])
    op.create_index('ix_usage_tracking_api_type', 'usage_tracking', ['api_type'])
    op.create_index('ix_usage_tracking_date', 'usage_tracking', ['date'])


def downgrade() -> None:
    op.drop_index('ix_usage_tracking_date', table_name='usage_tracking')
    op.drop_index('ix_usage_tracking_api_type', table_name='usage_tracking')
    op.drop_index('ix_usage_tracking_user_id', table_name='usage_tracking')
    op.drop_table('usage_tracking')

    # Drop enum type
    api_type = sa.Enum(name='apitype')
    api_type.drop(op.get_bind(), checkfirst=True)
