from sqlalchemy import Column, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from app.models.base_class import Base, TimestampMixin

class BuyerListing(Base, TimestampMixin):
    """
    Surplus listing created by asset operator after checking produce quality.
    Unapproved listings can NEVER be published or purchased by buyers.
    """
    __tablename__ = "buyer_listings"

    inventory_id = Column(String(36), ForeignKey("inventory.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_id = Column(String(36), ForeignKey("cold_assets.id", ondelete="CASCADE"), nullable=False, index=True)
    operator_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    crop_code = Column(String(50), nullable=False, index=True)

    initial_quantity_kg = Column(Float, nullable=False)
    available_quantity_kg = Column(Float, nullable=False)
    base_price_per_kg = Column(Float, nullable=False)
    current_discount_pct = Column(Float, default=0.0, nullable=False)
    discounted_price_per_kg = Column(Float, nullable=False)
    
    # Status: PENDING_APPROVAL, APPROVED, SOLD_OUT, CANCELLED
    status = Column(String(50), default="PENDING_APPROVAL", nullable=False, index=True)
    quality_approved_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    quality_approved_at = Column(DateTime(timezone=True), nullable=True)
    quality_grade = Column(String(50), default="GRADE_A", nullable=True)
    
    listed_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    inventory = relationship("Inventory", back_populates="listings")
    asset = relationship("ColdAsset")
    operator = relationship("User", foreign_keys=[operator_id])
    approver = relationship("User", foreign_keys=[quality_approved_by])
    orders = relationship("PurchaseOrder", back_populates="listing", cascade="all, delete-orphan")


class PurchaseOrder(Base, TimestampMixin):
    """
    Buyer purchase order against an approved surplus listing.
    PROTOTYPE NOTE: This is an order request with stock reservation.
    ZERO payment gateway or payment processing integration.
    """
    __tablename__ = "purchase_orders"

    listing_id = Column(String(36), ForeignKey("buyer_listings.id", ondelete="CASCADE"), nullable=False, index=True)
    buyer_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    quantity_kg = Column(Float, nullable=False)
    unit_price_inr = Column(Float, nullable=False)
    total_price_inr = Column(Float, nullable=False)

    # Status: REQUESTED, CONFIRMED, COMPLETED, CANCELLED
    status = Column(String(50), default="REQUESTED", nullable=False, index=True)
    delivery_preference = Column(String(50), default="BUYER_PICKUP", nullable=False) # BUYER_PICKUP, VAN_DELIVERY
    contact_phone = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    listing = relationship("BuyerListing", back_populates="orders")
    buyer = relationship("User", back_populates="orders")
