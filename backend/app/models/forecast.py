from sqlalchemy import Column, String, Float, Integer, Text
from app.models.base_class import Base, TimestampMixin

class DemandForecast(Base, TimestampMixin):
    """
    Demo baseline seasonal demand forecast by crop and district.
    PROTOTYPE HONESTY NOTE:
    Rule-based seasonal estimate based on historical Maharashtra mandi arrivals.
    NOT a trained machine learning model; NO confidence percentages implied.
    """
    __tablename__ = "demand_forecasts"

    crop_code = Column(String(50), nullable=False, index=True)
    district = Column(String(100), nullable=False, index=True)
    horizon_days = Column(Integer, default=7, nullable=False)
    estimated_demand_kg = Column(Float, nullable=False)
    price_trend = Column(String(50), default="STABLE", nullable=False) # RISING, STABLE, FALLING
    expected_price_inr_kg = Column(Float, nullable=False)
    forecast_source = Column(String(100), default="SEASONAL_RULE_BASED", nullable=False)
    notes = Column(Text, nullable=True)
