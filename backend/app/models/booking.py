from sqlalchemy import Column, String, Float, ForeignKey, DateTime, Integer
from sqlalchemy.orm import relationship
from app.models.base_class import Base, TimestampMixin

class Booking(Base, TimestampMixin):
    """
    Booking record managing capacity reservation and state transitions.
    Allowed states:
    REQUESTED, MATCHED, RESERVED, CONFIRMED, PICKUP_SCHEDULED, PRODUCE_RECEIVED,
    IN_STORAGE, COMPLETED, CANCELLED, EXPIRED, FAILED
    """
    __tablename__ = "bookings"

    request_id = Column(String(36), ForeignKey("matching_requests.id", ondelete="SET NULL"), nullable=True, index=True)
    batch_id = Column(String(36), ForeignKey("produce_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_id = Column(String(36), ForeignKey("cold_assets.id", ondelete="CASCADE"), nullable=False, index=True)
    farmer_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    quantity_kg = Column(Float, nullable=False)
    status = Column(String(50), default="RESERVED", nullable=False, index=True)
    reserved_until = Column(DateTime(timezone=True), nullable=True)
    estimated_total_inr = Column(Float, nullable=False, default=0.0)
    rate_per_kg_per_day = Column(Float, nullable=False, default=0.0)
    days_estimated = Column(Integer, nullable=False, default=1)
    status_updated_by = Column(String(36), nullable=True)

    request = relationship("MatchingRequest", back_populates="booking")
    batch = relationship("ProduceBatch", back_populates="bookings")
    asset = relationship("ColdAsset", back_populates="bookings")
    farmer = relationship("User", back_populates="bookings")
