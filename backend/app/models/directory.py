"""
ColdBridge AI - Public Cold Storage Directory Model (Part 4)

Stores public directory listings of real cold storage facilities in Nashik and Pune.
These are NOT ColdBridge partners and have zero foreign keys to assets, bookings, bids, or SRI.
"""

from sqlalchemy import Column, String, Float, Boolean, Date, UniqueConstraint
from app.models.base_class import Base, TimestampMixin


class PublicColdStorageListing(Base, TimestampMixin):
    __tablename__ = "public_cold_storage_listings"

    name = Column(String(255), nullable=False)
    district = Column(String(50), nullable=False)  # "Nashik" or "Pune"
    area = Column(String(255), nullable=False)
    address = Column(String(500), nullable=False)
    phone = Column(String(50), nullable=True)
    source_note = Column(String(500), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    capacity_mt = Column(Float, nullable=True)
    is_partner = Column(Boolean, default=False, nullable=False)
    contact_verified = Column(Boolean, default=False, nullable=False)
    last_checked_on = Column(Date, nullable=True)

    __table_args__ = (
        UniqueConstraint("name", "district", name="uq_public_cold_storage_name_district"),
    )
