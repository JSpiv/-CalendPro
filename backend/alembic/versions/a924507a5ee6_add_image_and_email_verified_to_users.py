"""add_image_and_email_verified_to_users

Revision ID: a924507a5ee6
Revises: 665911120415
Create Date: 2025-12-31 11:39:27.305601

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a924507a5ee6'
down_revision: Union[str, None] = '665911120415'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply migration."""
    # Add image and email_verified columns to users table for Auth.js compatibility
    op.add_column('users', sa.Column('email_verified', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('image', sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Rollback migration."""
    op.drop_column('users', 'image')
    op.drop_column('users', 'email_verified')
