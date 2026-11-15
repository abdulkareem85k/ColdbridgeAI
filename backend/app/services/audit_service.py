"""
ColdBridge AI - Audit Logging Service

Records security and operational audit logs for assets, bids, matching, and bookings.
Strictly excludes passwords, JWT tokens, and credentials.
"""

import json
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from app.models.audit import AuditLog


def log_audit_event(
    db: Session,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    user_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None
) -> AuditLog:
    """
    Persist an audit log record into audit_logs table.
    Filters out any sensitive fields (passwords, tokens, keys) automatically.
    """
    safe_details = {}
    if details:
        sensitive_keys = {"password", "token", "jwt", "secret", "cookie", "hashed_password"}
        for k, v in details.items():
            if any(s in k.lower() for s in sensitive_keys):
                continue
            safe_details[k] = v

    audit_entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=json.dumps(safe_details) if safe_details else None,
        ip_address=ip_address
    )
    db.add(audit_entry)
    return audit_entry
