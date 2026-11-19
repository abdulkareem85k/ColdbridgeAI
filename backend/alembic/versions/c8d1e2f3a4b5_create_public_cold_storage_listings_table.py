"""create_public_cold_storage_listings_table

Revision ID: c8d1e2f3a4b5
Revises: b6f914b3b6de
Create Date: 2026-11-18 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8d1e2f3a4b5'
down_revision: Union[str, Sequence[str], None] = 'b6f914b3b6de'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'public_cold_storage_listings',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('district', sa.String(length=50), nullable=False),
        sa.Column('area', sa.String(length=255), nullable=False),
        sa.Column('address', sa.String(length=500), nullable=False),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('source_note', sa.String(length=500), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('capacity_mt', sa.Float(), nullable=True),
        sa.Column('is_partner', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('contact_verified', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('last_checked_on', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', 'district', name='uq_public_cold_storage_name_district')
    )
    op.create_index(
        op.f('ix_public_cold_storage_listings_id'),
        'public_cold_storage_listings',
        ['id'],
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f('ix_public_cold_storage_listings_id'),
        table_name='public_cold_storage_listings'
    )
    op.drop_table('public_cold_storage_listings')
