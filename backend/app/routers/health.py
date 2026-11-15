import datetime
from datetime import timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.config import settings
from app.db.session import get_db

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("")
def get_health(db: Session = Depends(get_db)):
    """Health check endpoint verifying backend runtime and DB connectivity."""
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "ok",
        "app_env": settings.APP_ENV,
        "database": db_status,
        "timestamp": datetime.datetime.now(timezone.utc).isoformat()
    }
