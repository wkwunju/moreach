"""Add is_blocked field to users table

Revision ID: 0003
Revises: 0002
Create Date: 2026-02-07

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade():
    # Check if column already exists (e.g. from create_all())
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT EXISTS(SELECT 1 FROM information_schema.columns "
        "WHERE table_name = 'users' AND column_name = 'is_blocked')"
    ))
    if result.scalar():
        return

    # Add is_blocked column with default False
    op.add_column('users', sa.Column('is_blocked', sa.Boolean(), nullable=False, server_default='false'))


def downgrade():
    op.drop_column('users', 'is_blocked')
