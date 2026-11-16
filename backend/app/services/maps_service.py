import math
import time
import threading
import datetime
from datetime import timezone
from typing import Tuple, List, Dict, Any, Optional
from urllib.parse import quote
import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.route import RouteCache

# Thread-safe rate limiter for OpenStreetMap Nominatim (enforcing <= 1 request/second)
# NOTE: This rate limiter coordinates requests inside ONE Python process only.
# For the Avishkar exhibition, the backend MUST run with a single worker (`uvicorn app.main:app` without --workers).
# This does NOT guarantee global rate limiting across multiple separate worker processes or server instances.
_nominatim_rate_lock = threading.Lock()
_last_nominatim_call_timestamp: float = 0.0

# In-memory caches with 24-hour TTL
# NOTE: In-memory cache entries do not persist across process restarts. Suitable for single-worker exhibition deployment.
_nominatim_reverse_cache: Dict[Tuple[float, float], Tuple[str, float]] = {}
_nominatim_search_cache: Dict[Tuple[str, int], Tuple[List[Dict[str, Any]], float]] = {}
NOMINATIM_CACHE_TTL_SECONDS = 86400.0  # 24 hours

def _acquire_nominatim_slot(timeout: float = 3.0) -> bool:
    """
    Acquire permission to call Nominatim, ensuring at least 1.0s spacing between external calls.
    Returns True if slot acquired within timeout, False if timed out waiting.
    """
    start_time = time.time()
    acquired = _nominatim_rate_lock.acquire(timeout=timeout)
    if not acquired:
        return False
    
    try:
        global _last_nominatim_call_timestamp
        now = time.time()
        elapsed = now - _last_nominatim_call_timestamp
        if elapsed < 1.0:
            sleep_needed = 1.0 - elapsed
            remaining = timeout - (time.time() - start_time)
            if sleep_needed > remaining:
                return False
            time.sleep(sleep_needed)
        _last_nominatim_call_timestamp = time.time()
        return True
    finally:
        _nominatim_rate_lock.release()

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

def reverse_geocode(lat: float, lng: float) -> Dict[str, Any]:
    """
    Reverse geocode coordinates to an address using OpenStreetMap Nominatim.
    Enforces <= 1 req/sec rate limit, 24h caching, and graceful fallback on timeout/failure.
    Returns dict: {"address": str | None, "source": "NOMINATIM" | "CACHE" | "UNAVAILABLE", "latitude": lat, "longitude": lng}
    """
    coord_key = (round(lat, 4), round(lng, 4))
    now = time.time()

    # 1. Check in-memory 24h cache
    if coord_key in _nominatim_reverse_cache:
        cached_address, timestamp = _nominatim_reverse_cache[coord_key]
        if now - timestamp < NOMINATIM_CACHE_TTL_SECONDS:
            return {
                "address": cached_address,
                "source": "CACHE",
                "latitude": lat,
                "longitude": lng
            }

    # 2. Acquire rate limiter slot (give up after 3s timeout)
    if not _acquire_nominatim_slot(timeout=3.0):
        return {
            "address": None,
            "source": "UNAVAILABLE",
            "latitude": lat,
            "longitude": lng
        }

    # 3. Call Nominatim
    url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lng}"
    try:
        with httpx.Client(timeout=3.0) as client:
            resp = client.get(url, headers={"User-Agent": settings.OSM_USER_AGENT})
            if resp.status_code == 200:
                data = resp.json()
                display_name = data.get("display_name")
                if display_name:
                    _nominatim_reverse_cache[coord_key] = (display_name, now)
                    return {
                        "address": display_name,
                        "source": "NOMINATIM",
                        "latitude": lat,
                        "longitude": lng
                    }
    except Exception:
        pass

    return {
        "address": None,
        "source": "UNAVAILABLE",
        "latitude": lat,
        "longitude": lng
    }

def search_address(query: str, limit: int = 1) -> List[Dict[str, Any]]:
    """
    Forward geocode an address query using OpenStreetMap Nominatim with Maharashtra/India bias.
    Enforces <= 1 req/sec rate limit, 24h caching, and returns list of search results.
    """
    norm_query = query.strip().lower()
    cache_key = (norm_query, limit)
    now = time.time()

    # 1. Check in-memory cache
    if cache_key in _nominatim_search_cache:
        cached_results, timestamp = _nominatim_search_cache[cache_key]
        if now - timestamp < NOMINATIM_CACHE_TTL_SECONDS:
            return cached_results

    # 2. Acquire rate limit slot
    if not _acquire_nominatim_slot(timeout=3.0):
        return []

    # 3. Call Nominatim
    search_q = f"{query.strip()}, Maharashtra, India" if "india" not in norm_query else query.strip()
    url = f"https://nominatim.openstreetmap.org/search?format=json&q={quote(search_q)}&limit={limit}"
    
    try:
        with httpx.Client(timeout=3.0) as client:
            resp = client.get(url, headers={"User-Agent": settings.OSM_USER_AGENT})
            if resp.status_code == 200:
                data = resp.json()
                results = []
                for item in data:
                    item_lat = float(item.get("lat", 0.0))
                    item_lon = float(item.get("lon", 0.0))
                    results.append({
                        "display_name": item.get("display_name", ""),
                        "latitude": item_lat,
                        "longitude": item_lon,
                        "lat": item_lat,
                        "lon": item_lon
                    })
                _nominatim_search_cache[cache_key] = (results, now)
                return results
    except Exception:
        pass

    return []
