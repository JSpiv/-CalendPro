"""add_authjs_tables

Revision ID: 665911120415
Revises: 66d7ada37c79
Create Date: 2025-12-30 18:36:49.168088

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '665911120415'
down_revision: Union[str, None] = '66d7ada37c79'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add missing columns to oauth_accounts for Auth.js compatibility
    op.add_column('oauth_accounts', sa.Column('type', sa.String(length=50), nullable=True))
    op.add_column('oauth_accounts', sa.Column('token_type', sa.String(length=50), nullable=True))
    op.add_column('oauth_accounts', sa.Column('scope', sa.String(), nullable=True))
    op.add_column('oauth_accounts', sa.Column('id_token', sa.Text(), nullable=True))
    op.add_column('oauth_accounts', sa.Column('session_state', sa.String(), nullable=True))
    op.add_column('oauth_accounts', sa.Column('expires_at', sa.Integer(), nullable=True))

    # Add unique constraint required by Auth.js
    op.create_unique_constraint('uq_oauth_accounts_provider_provider_account_id', 'oauth_accounts', ['provider', 'provider_account_id'])

    # Create sessions table
    op.create_table(
        'sessions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('session_token', sa.String(length=255), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('expires', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_token')
    )

    # Create verification_tokens table
    op.create_table(
        'verification_tokens',
        sa.Column('identifier', sa.String(length=255), nullable=False),
        sa.Column('token', sa.String(length=255), nullable=False),
        sa.Column('expires', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('identifier', 'token'),
        sa.UniqueConstraint('token')
    )


def downgrade() -> None:
    # Use IF EXISTS to avoid errors if tables don't exist
    op.execute("DROP TABLE IF EXISTS verification_tokens")
    op.execute("DROP TABLE IF EXISTS sessions")

    # Drop constraint only if it exists
    op.execute("ALTER TABLE oauth_accounts DROP CONSTRAINT IF EXISTS uq_oauth_accounts_provider_provider_account_id")

    # Drop columns only if they exist
    for col in ['expires_at', 'session_state', 'id_token', 'scope', 'token_type', 'type']:
        op.execute(f"ALTER TABLE oauth_accounts DROP COLUMN IF EXISTS {col}")
