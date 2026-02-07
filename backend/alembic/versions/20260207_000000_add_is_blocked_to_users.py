"""Add is_blocked field to users table

Revision ID: 20260207_000000
Revises: 20260204_000000
Create Date: 2026-02-07

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260207_000000'
down_revision = '20260204_000000'
branch_labels = None
depends_on = None


def upgrade():
    # Add is_blocked column with default False
    op.add_column('users', sa.Column('is_blocked', sa.Boolean(), nullable=False, server_default='false'))


def downgrade():
    op.drop_column('users', 'is_blocked')
