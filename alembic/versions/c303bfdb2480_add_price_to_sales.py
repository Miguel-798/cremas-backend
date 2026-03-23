"""add_price_to_sales

Revision ID: c303bfdb2480
Revises: add_price_to_creams
Create Date: 2026-03-22 21:24:37.590110

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c303bfdb2480'
down_revision: Union[str, Sequence[str], None] = 'add_price_to_creams'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('sales', sa.Column('price', sa.Numeric(10, 2), nullable=False, server_default='0.00'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('sales', 'price')
