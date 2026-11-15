from sqlalchemy import Column, Float, String, Text
from app.models.base_class import Base, TimestampMixin

class RouteCache(Base, TimestampMixin):
    """
    Route calculation cache.
    Coordinates rounded to 4 decimals for query lookup.
    TTL governed by ROUTE_CACHE_MINUTES.
    Route source: OSRM_ROUTES or ESTIMATED.
    """
    __tablename__ = "route_cache"

    origin_lat = Column(Float, nullable=False, index=True)
    origin_lng = Column(Float, nullable=False, index=True)
    dest_lat = Column(Float, nullable=False, index=True)
    dest_lng = Column(Float, nullable=False, index=True)
    distance_km = Column(Float, nullable=False)
    duration_minutes = Column(Float, nullable=False)
    encoded_polyline = Column(Text, nullable=True)
    route_source = Column(String(50), default="ESTIMATED", nullable=False)  # OSRM_ROUTES or ESTIMATED
