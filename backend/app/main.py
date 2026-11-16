from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import (
    health, auth, profiles, produce, assets, maps, sri, matching, bookings, admin,
    inventory, marketplace, forecast
)

app = FastAPI(
    title="ColdBridge AI API",
    description="AI-driven pay-per-use cold-chain logistics and aggregation platform (OpenStreetMap + Leaflet.js edition)",
    version="1.1.0"
)

# Configure CORS strictly to FRONTEND_ORIGIN (supports comma-separated list, no wildcards, credentials on)
raw_origins = [o.strip() for o in settings.FRONTEND_ORIGIN.split(",") if o.strip()]
origins = []
for orig in raw_origins:
    if orig == "*":
        continue  # Wildcards strictly prohibited when allow_credentials=True
    if orig not in origins:
        origins.append(orig)
    # Pair localhost and 127.0.0.1 only in development / testing environments
    if settings.APP_ENV != "production":
        if "127.0.0.1" in orig:
            paired = orig.replace("127.0.0.1", "localhost")
            if paired not in origins:
                origins.append(paired)
        elif "localhost" in orig:
            paired = orig.replace("localhost", "127.0.0.1")
            if paired not in origins:
                origins.append(paired)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 Routers
API_V1_PREFIX = "/api/v1"
app.include_router(health.router, prefix=API_V1_PREFIX)
app.include_router(auth.router, prefix=API_V1_PREFIX)
app.include_router(profiles.router, prefix=API_V1_PREFIX)
app.include_router(produce.router, prefix=API_V1_PREFIX)
app.include_router(assets.router, prefix=API_V1_PREFIX)
app.include_router(maps.router, prefix=API_V1_PREFIX)
app.include_router(sri.router, prefix=API_V1_PREFIX)
app.include_router(matching.router, prefix=API_V1_PREFIX)
app.include_router(bookings.router, prefix=API_V1_PREFIX)
app.include_router(admin.router, prefix=API_V1_PREFIX)
app.include_router(inventory.router, prefix=API_V1_PREFIX)
app.include_router(marketplace.router, prefix=API_V1_PREFIX)
app.include_router(forecast.router, prefix=API_V1_PREFIX)

@app.get("/")
def root():
    return {
        "name": "ColdBridge AI API",
        "version": "1.1.0",
        "maps_platform": "OpenStreetMap + Leaflet.js",
        "docs_url": "/docs",
        "health_url": f"{API_V1_PREFIX}/health"
    }
