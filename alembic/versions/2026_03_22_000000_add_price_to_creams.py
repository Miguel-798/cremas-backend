"""add_price_to_creams

Revision ID: add_price_to_creams
Revises: 5108831d33a7
Create Date: 2026-03-22 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_price_to_creams'
down_revision: Union[str, Sequence[str], None] = '5108831d33a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add price column to creams table."""
    op.add_column('creams', sa.Column('price', sa.Numeric(10, 2), nullable=False, server_default='0.00'))


def downgrade() -> None:
    """Remove price column from creams table."""
    op.drop_column('creams', 'price')
