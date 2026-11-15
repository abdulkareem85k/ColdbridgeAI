import datetime
from datetime import timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.forecast import DemandForecast

DEFAULT_SEASONAL_ESTIMATES = [
    {
        "crop_code": "mango",
        "district": "Ratnagiri",
        "horizon_days": 7,
        "estimated_demand_kg": 25000.0,
        "price_trend": "RISING",
        "expected_price_inr_kg": 120.0,
        "notes": "Peak Alphonso export season in Konkan belt. High demand for pre-cooled fruit."
    },
    {
        "crop_code": "tomato",
        "district": "Nashik",
        "horizon_days": 7,
        "estimated_demand_kg": 40000.0,
        "price_trend": "FALLING",
        "expected_price_inr_kg": 22.0,
        "notes": "Heavy mandi arrivals in Pimpalgaon market. Significant cold storage buffer required."
    },
    {
        "crop_code": "grapes",
        "district": "Nashik",
        "horizon_days": 14,
        "estimated_demand_kg": 35000.0,
        "price_trend": "STABLE",
        "expected_price_inr_kg": 85.0,
        "notes": "Table grapes cold aggregation for domestic metros."
    },
    {
        "crop_code": "onion",
        "district": "Pune",
        "horizon_days": 30,
        "estimated_demand_kg": 60000.0,
        "price_trend": "RISING",
        "expected_price_inr_kg": 35.0,
        "notes": "Post-monsoon storage demand in Gultekdi wholesale market."
    },
    {
        "crop_code": "strawberry",
        "district": "Pune",
        "horizon_days": 3,
        "estimated_demand_kg": 8000.0,
        "price_trend": "RISING",
        "expected_price_inr_kg": 180.0,
        "notes": "Mahabaleshwar-Pune transit corridor. Rapid perishable turnover."
    },
    {
        "crop_code": "pomegranate",
        "district": "Solapur",
        "horizon_days": 14,
        "estimated_demand_kg": 20000.0,
        "price_trend": "STABLE",
        "expected_price_inr_kg": 110.0,
        "notes": "Bhagwa export and domestic packing aggregation."
    }
]

def seed_default_forecasts(db: Session):
    """
    Ensure baseline rule-based seasonal forecasts exist in the database.
    """
    existing_count = db.query(DemandForecast).count()
    if existing_count == 0:
        for est in DEFAULT_SEASONAL_ESTIMATES:
            fc = DemandForecast(
                crop_code=est["crop_code"],
                district=est["district"],
                horizon_days=est["horizon_days"],
                estimated_demand_kg=est["estimated_demand_kg"],
                price_trend=est["price_trend"],
                expected_price_inr_kg=est["expected_price_inr_kg"],
                forecast_source="SEASONAL_RULE_BASED",
                notes=est["notes"]
            )
            db.add(fc)
        db.commit()


def get_forecasts(
    db: Session,
    crop_code: Optional[str] = None,
    district: Optional[str] = None
) -> List[DemandForecast]:
    """
    Query demand forecasts with optional filters.
    """
    seed_default_forecasts(db)
    query = db.query(DemandForecast)
    if crop_code:
        query = query.filter(DemandForecast.crop_code.ilike(f"%{crop_code}%"))
    if district:
        query = query.filter(DemandForecast.district.ilike(f"%{district}%"))
    return query.order_by(DemandForecast.district, DemandForecast.crop_code).all()
