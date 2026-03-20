"""initial schema with indexes

Revision ID: 5108831d33a7
Revises: 
Create Date: 2026-03-20 12:34:51.141194

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '5108831d33a7'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add database indexes for performance optimization."""
    # creams table indexes
    op.create_index('ix_creams_quantity', 'creams', ['quantity'], unique=False)
    op.create_index('ix_creams_updated_at', 'creams', ['updated_at'], unique=False)
    
    # sales table indexes
    op.create_index('ix_sales_cream_id', 'sales', ['cream_id'], unique=False)
    op.create_index('ix_sales_sold_at', 'sales', ['sold_at'], unique=False)
    
    # reservations table indexes
    op.create_index('ix_reservations_cream_id', 'reservations', ['cream_id'], unique=False)
    op.create_index('ix_reservations_is_active', 'reservations', ['is_active'], unique=False)
    op.create_index('ix_reservations_reserved_for', 'reservations', ['reserved_for'], unique=False)
    op.create_index('ix_reservations_active_date', 'reservations', ['is_active', 'reserved_for'], unique=False)


def downgrade() -> None:
    """Remove database indexes."""
    op.drop_index('ix_reservations_active_date', table_name='reservations')
    op.drop_index('ix_reservations_reserved_for', table_name='reservations')
    op.drop_index('ix_reservations_is_active', table_name='reservations')
    op.drop_index('ix_reservations_cream_id', table_name='reservations')
    op.drop_index('ix_sales_sold_at', table_name='sales')
    op.drop_index('ix_sales_cream_id', table_name='sales')
    op.drop_index('ix_creams_updated_at', table_name='creams')
    op.drop_index('ix_creams_quantity', table_name='creams')
