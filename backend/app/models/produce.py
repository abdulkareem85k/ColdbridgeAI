from sqlalchemy import Column, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from app.models.base_class import Base, TimestampMixin

class ProduceBatch(Base, TimestampMixin):
    __tablename__ = "produce_batches"

    farmer_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    crop_code = Column(String(100), nullable=False)
    quantity_kg = Column(Float, nullable=False)
    harvest_at = Column(DateTime(timezone=True), nullable=False)
    ambient_temp_c = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    notes = Column(Text, nullable=True)
    data_source = Column(String(50), default="SIMULATED", nullable=False)  # SIMULATED or LIVE

    farmer = relationship("User", back_populates="batches")
    assessments = relationship("SpoilageAssessment", back_populates="batch", cascade="all, delete-orphan")
    matching_requests = relationship("MatchingRequest", back_populates="batch", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="batch", cascade="all, delete-orphan")

class SpoilageAssessment(Base, TimestampMixin):
    """
    Transparent rule-based prototype Spoilage Risk Index (SRI) assessment.
    NOTE: Not a scientifically validated prediction.
    """
    __tablename__ = "spoilage_assessments"

    batch_id = Column(String(36), ForeignKey("produce_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    score = Column(Float, nullable=False)
    risk_category = Column(String(50), nullable=False)  # HIGH, MEDIUM, LOW
    reasons = Column(Text, nullable=False)  # JSON-encoded array of plain-English reasons
    factors = Column(Text, nullable=False)  # JSON-encoded dict of factors evaluated
    recommended_action = Column(String(255), nullable=False)
    rule_version = Column(String(50), default="prototype-1", nullable=False)

    batch = relationship("ProduceBatch", back_populates="assessments")
