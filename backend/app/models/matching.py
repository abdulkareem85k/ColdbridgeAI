from sqlalchemy import Column, String, Float, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from app.models.base_class import Base, TimestampMixin

class MatchingRequest(Base, TimestampMixin):
    __tablename__ = "matching_requests"

    batch_id = Column(String(36), ForeignKey("produce_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    farmer_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    requested_quantity_kg = Column(Float, nullable=False)
    status = Column(String(50), default="PENDING", nullable=False)  # PENDING, MATCHED, ALLOCATED, CANCELLED

    batch = relationship("ProduceBatch", back_populates="matching_requests")
    farmer = relationship("User")
    bids = relationship("Bid", back_populates="request", cascade="all, delete-orphan")
    booking = relationship("Booking", back_populates="request", uselist=False)

class Bid(Base, TimestampMixin):
    __tablename__ = "bids"

    request_id = Column(String(36), ForeignKey("matching_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_id = Column(String(36), ForeignKey("cold_assets.id", ondelete="CASCADE"), nullable=False, index=True)
    offered_capacity_kg = Column(Float, nullable=False)
    price_total = Column(Float, nullable=False)
    eta_minutes = Column(Float, nullable=False)
    valid_until = Column(DateTime(timezone=True), nullable=False)
    score = Column(Float, nullable=True)
    note = Column(Text, nullable=True)
    data_source = Column(String(50), default="SIMULATED", nullable=False)
    is_accepted = Column(Boolean, default=False, nullable=False)
    is_expired = Column(Boolean, default=False, nullable=False)

    request = relationship("MatchingRequest", back_populates="bids")
    asset = relationship("ColdAsset", back_populates="bids")
