from sqlalchemy import Column, String, Float, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from app.models.base_class import Base, TimestampMixin

class Inventory(Base, TimestampMixin):
    """
    Facility inventory record created when a booking reaches PRODUCE_RECEIVED.
    Links directly to produce batch and booking with quantity traceability.
    """
    __tablename__ = "inventory"

    batch_id = Column(String(36), ForeignKey("produce_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    booking_id = Column(String(36), ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_id = Column(String(36), ForeignKey("cold_assets.id", ondelete="CASCADE"), nullable=False, index=True)
    farmer_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    initial_quantity_kg = Column(Float, nullable=False)
    current_quantity_kg = Column(Float, nullable=False)
    storage_location = Column(String(100), default="Main Bay", nullable=False)
    received_at = Column(DateTime(timezone=True), nullable=False)
    expiry_risk_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="STORED", nullable=False, index=True) # STORED, NEAR_EXPIRY, SURPLUS_LISTED, DISPATCHED
    quality_notes = Column(Text, nullable=True)

    batch = relationship("ProduceBatch")
    booking = relationship("Booking")
    asset = relationship("ColdAsset")
    farmer = relationship("User")
    listings = relationship("BuyerListing", back_populates="inventory", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="inventory", cascade="all, delete-orphan")


class Alert(Base, TimestampMixin):
    """
    Operational and near-expiry alert records for operators and farmers.
    """
    __tablename__ = "alerts"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_id = Column(String(36), ForeignKey("cold_assets.id", ondelete="CASCADE"), nullable=True, index=True)
    batch_id = Column(String(36), ForeignKey("produce_batches.id", ondelete="CASCADE"), nullable=True, index=True)
    inventory_id = Column(String(36), ForeignKey("inventory.id", ondelete="CASCADE"), nullable=True, index=True)

    alert_type = Column(String(100), nullable=False, index=True) # NEAR_EXPIRY_WARNING, SURPLUS_RECOMMENDED, QUALITY_APPROVAL_REQUIRED
    severity = Column(String(50), default="WARNING", nullable=False) # INFO, WARNING, CRITICAL
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)

    user = relationship("User")
    asset = relationship("ColdAsset")
    batch = relationship("ProduceBatch")
    inventory = relationship("Inventory", back_populates="alerts")
