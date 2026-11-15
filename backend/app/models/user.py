from sqlalchemy import Column, String, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base_class import Base, TimestampMixin

class User(Base, TimestampMixin):
    __tablename__ = "users"

    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, index=True)  # FARMER, STATIC_OPERATOR, VAN_OPERATOR, BUYER, ADMIN
    full_name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    farmer_profile = relationship("FarmerProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    operator_profile = relationship("OperatorProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    buyer_profile = relationship("BuyerProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    batches = relationship("ProduceBatch", back_populates="farmer", cascade="all, delete-orphan")
    assets = relationship("ColdAsset", back_populates="operator", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="farmer", cascade="all, delete-orphan")
    orders = relationship("PurchaseOrder", back_populates="buyer", cascade="all, delete-orphan")

class FarmerProfile(Base, TimestampMixin):
    __tablename__ = "farmer_profiles"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    farm_name = Column(String(255), nullable=False)
    district = Column(String(100), nullable=False)
    state = Column(String(100), default="Maharashtra", nullable=False)
    default_latitude = Column(Float, nullable=True)
    default_longitude = Column(Float, nullable=True)

    user = relationship("User", back_populates="farmer_profile")

class OperatorProfile(Base, TimestampMixin):
    __tablename__ = "operator_profiles"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    business_name = Column(String(255), nullable=False)
    contact_phone = Column(String(50), nullable=True)
    district = Column(String(100), nullable=False)
    state = Column(String(100), default="Maharashtra", nullable=False)

    user = relationship("User", back_populates="operator_profile")

class BuyerProfile(Base, TimestampMixin):
    __tablename__ = "buyer_profiles"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    business_name = Column(String(255), nullable=False)
    buyer_type = Column(String(100), default="WHOLESALER", nullable=False)
    contact_phone = Column(String(50), nullable=True)
    address = Column(String(500), nullable=True)
    district = Column(String(100), nullable=False)
    state = Column(String(100), default="Maharashtra", nullable=False)

    user = relationship("User", back_populates="buyer_profile")
