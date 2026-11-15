import math
import datetime
from datetime import timezone
from typing import Tuple, List, Dict, Any, Optional
import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.route import RouteCache

# In-memory counter for daily safety call capping
_daily_routing_calls: Dict[str, int] = {}

def get_today_key() -> str:
    return datetime.datetime.now(timezone.utc).strftime("%Y-%m-%d")

def increment_daily_calls() -> int:
    today = get_today_key()
    current = _daily_routing_calls.get(today, 0) + 1
    _daily_routing_calls[today] = current
    return current

def get_daily_calls() -> int:
    today = get_today_key()
    return _daily_routing_calls.get(today, 0)

def haversine_km(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    """
    Calculate the great circle distance in kilometers between two points
    on the earth (specified in decimal degrees).
    """
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    radius = 6371.0 # Earth's mean radius in km

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(radius * c, 2)

def compute_route(
    origin: Tuple[float, float],
    destination: Tuple[float, float],
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Compute driving route distance (km), duration (minutes), and coordinates
    using OpenStreetMap / OSRM routing with intelligent SQLite/Postgres caching and straight-line fallback.
    """
    orig_lat, orig_lng = round(origin[0], 4), round(origin[1], 4)
    dest_lat, dest_lng = round(destination[0], 4), round(destination[1], 4)
    now_utc = datetime.datetime.now(timezone.utc)

    # 1. Check Route Cache
    if db is not None:
        cached = db.query(RouteCache).filter(
            RouteCache.origin_lat == orig_lat,
            RouteCache.origin_lng == orig_lng,
            RouteCache.dest_lat == dest_lat,
            RouteCache.dest_lng == dest_lng
        ).first()

        if cached:
            # Check TTL
            cache_age = now_utc - cached.updated_at.replace(tzinfo=timezone.utc) if cached.updated_at.tzinfo is None else (now_utc - cached.updated_at)
            if cache_age <= datetime.timedelta(minutes=settings.ROUTE_CACHE_MINUTES):
                return {
                    "distance_km": cached.distance_km,
                    "duration_minutes": cached.duration_minutes,
                    "encoded_polyline": cached.encoded_polyline,
                    "route_source": cached.route_source,
                    "cached": True
                }

    # 2. Check Daily Safety Cap
    daily_count = get_daily_calls()
    if daily_count >= settings.MAX_ROUTE_CALLS_PER_DAY:
        # Fallback to straight-line haversine estimate
        dist = haversine_km((orig_lat, orig_lng), (dest_lat, dest_lng))
        # Estimate duration assuming average speed of 40 km/h plus 10 min setup
        est_duration = round((dist / 40.0) * 60.0 + 10.0, 1)
        return {
            "distance_km": dist,
            "duration_minutes": est_duration,
            "encoded_polyline": None,
            "route_source": "ESTIMATED",
            "cached": False,
            "note": "Safety daily route call limit reached; using straight-line estimate."
        }

    # 3. Call OpenStreetMap OSRM Public Routing API
    # Note: OSRM expects coordinates in {lon},{lat} order!
    url = f"{settings.OSRM_ROUTING_URL}/route/v1/driving/{orig_lng},{orig_lat};{dest_lng},{dest_lat}?overview=full&geometries=geojson"
    
    distance_km = None
    duration_min = None
    polyline_geojson = None
    source = "ESTIMATED"

    try:
        increment_daily_calls()
        with httpx.Client(timeout=4.0) as client:
            resp = client.get(url, headers={"User-Agent": settings.OSM_USER_AGENT})
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == "Ok" and data.get("routes"):
                    first_route = data["routes"][0]
                    distance_km = round(first_route["distance"] / 1000.0, 2)
                    duration_min = round(first_route["duration"] / 60.0, 1)
                    polyline_geojson = str(first_route.get("geometry", {}).get("coordinates", []))
                    source = "OSRM_ROUTES"
    except Exception:
        # Fallback to haversine estimate if network times out or OSRM is unreachable
        pass

    if distance_km is None:
        distance_km = haversine_km((orig_lat, orig_lng), (dest_lat, dest_lng))
        duration_min = round((distance_km / 40.0) * 60.0 + 10.0, 1)
        source = "ESTIMATED"

    # 4. Save to Cache
    if db is not None:
        try:
            cached_entry = db.query(RouteCache).filter(
                RouteCache.origin_lat == orig_lat,
                RouteCache.origin_lng == orig_lng,
                RouteCache.dest_lat == dest_lat,
                RouteCache.dest_lng == dest_lng
            ).first()

            if cached_entry:
                cached_entry.distance_km = distance_km
                cached_entry.duration_minutes = duration_min
                cached_entry.encoded_polyline = polyline_geojson
                cached_entry.route_source = source
                cached_entry.updated_at = now_utc
            else:
                db.add(RouteCache(
                    origin_lat=orig_lat,
                    origin_lng=orig_lng,
                    dest_lat=dest_lat,
                    dest_lng=dest_lng,
                    distance_km=distance_km,
                    duration_minutes=duration_min,
                    encoded_polyline=polyline_geojson,
                    route_source=source
                ))
            db.commit()
        except Exception:
            db.rollback()

    return {
        "distance_km": distance_km,
        "duration_minutes": duration_min,
        "encoded_polyline": polyline_geojson,
        "route_source": source,
        "cached": False
    }

def compute_route_matrix(
    origin: Tuple[float, float],
    destinations: List[Tuple[float, float]],
    db: Optional[Session] = None
) -> List[Dict[str, Any]]:
    """
    Compute routes for multiple candidate destinations up to MAX_ROUTE_CALLS_PER_REQUEST.
    Picks nearest by straight-line distance first.
    """
    capped_dests = destinations[:settings.MAX_ROUTE_CALLS_PER_REQUEST]
    results = []
    for dest in capped_dests:
        route = compute_route(origin, dest, db)
        results.append(route)
    return results

def reverse_geocode(lat: float, lng: float) -> str:
    """
    Reverse geocode coordinates to a readable address using OpenStreetMap Nominatim.
    Respects OSM 1 request/sec rate policy with sensible fallbacks.
    """
    url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lng}"
    try:
        with httpx.Client(timeout=3.0) as client:
            resp = client.get(url, headers={"User-Agent": settings.OSM_USER_AGENT})
            if resp.status_code == 200:
                data = resp.json()
                display_name = data.get("display_name")
                if display_name:
                    return display_name
    except Exception:
        pass
    return f"Location ({lat:.4f}, {lng:.4f})"
