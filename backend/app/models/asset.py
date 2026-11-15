from sqlalchemy import Column, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.models.base_class import Base, TimestampMixin

class ColdAsset(Base, TimestampMixin):
    __tablename__ = "cold_assets"

    operator_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    asset_type = Column(String(50), nullable=False)  # STATIC or MOBILE
    total_capacity_kg = Column(Float, nullable=False)
    available_capacity_kg = Column(Float, nullable=False)
    price_per_kg_per_day = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    data_source = Column(String(50), default="SIMULATED", nullable=False)  # SIMULATED or LIVE

    operator = relationship("User", back_populates="assets")
    static_detail = relationship("StaticAssetDetail", back_populates="asset", uselist=False, cascade="all, delete-orphan")
    mobile_detail = relationship("MobileAssetDetail", back_populates="asset", uselist=False, cascade="all, delete-orphan")
    availabilities = relationship("AssetAvailability", back_populates="asset", cascade="all, delete-orphan")
    bids = relationship("Bid", back_populates="asset", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="asset", cascade="all, delete-orphan")

class StaticAssetDetail(Base, TimestampMixin):
    __tablename__ = "static_asset_details"

    asset_id = Column(String(36), ForeignKey("cold_assets.id", ondelete="CASCADE"), unique=True, nullable=False)
    supported_crops = Column(String(500), nullable=False)  # Comma-separated or JSON string
    min_temperature_c = Column(Float, nullable=False)
    max_temperature_c = Column(Float, nullable=False)
    address = Column(String(500), nullable=True)

    asset = relationship("ColdAsset", back_populates="static_detail")

class MobileAssetDetail(Base, TimestampMixin):
    """
    Mobile cooling van details.
    NOTE: solar_reliability is a SIMULATION INPUT (0.0 to 1.0), not a measured telemetry reading.
    Real battery, Peltier power and hardware telemetry belong to a later hardware phase and are not included in Phase 1.
    """
    __tablename__ = "mobile_asset_details"

    asset_id = Column(String(36), ForeignKey("cold_assets.id", ondelete="CASCADE"), unique=True, nullable=False)
    vehicle_ref = Column(String(100), nullable=False)
    service_radius_km = Column(Float, nullable=False)
    solar_reliability = Column(Float, default=0.9, nullable=False)  # Simulation input 0.0 - 1.0
    last_location_at = Column(DateTime(timezone=True), nullable=True)

    asset = relationship("ColdAsset", back_populates="mobile_detail")

class AssetAvailability(Base, TimestampMixin):
    __tablename__ = "asset_availability"

    asset_id = Column(String(36), ForeignKey("cold_assets.id", ondelete="CASCADE"), nullable=False, index=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    is_available = Column(Boolean, default=True, nullable=False)

    asset = relationship("ColdAsset", back_populates="availabilities")
