import datetime
from datetime import timezone
import uuid
from sqlalchemy import Column, String, DateTime, Text
from app.models.base_class import Base

class AuditLog(Base):
    """
    Audit log for tracking operations, logins, capacity changes, and bookings.
    Passswords and secrets are strictly excluded.
    """
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String(36), nullable=True, index=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(String(36), nullable=True)
    details = Column(Text, nullable=True)  # JSON-encoded payload
    ip_address = Column(String(50), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(timezone.utc),
        nullable=False
    )
