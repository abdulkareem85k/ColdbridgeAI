from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import health, auth, profiles, produce, assets, maps, sri

app = FastAPI(
    title="ColdBridge AI API",
    description="AI-driven pay-per-use cold-chain logistics and aggregation platform (OpenStreetMap + Leaflet.js edition)",
    version="1.1.0"
)

# Configure CORS strictly to FRONTEND_ORIGIN with credentials
origins = [settings.FRONTEND_ORIGIN]
if "127.0.0.1" in settings.FRONTEND_ORIGIN:
    origins.append(settings.FRONTEND_ORIGIN.replace("127.0.0.1", "localhost"))

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

@app.get("/")
def root():
    return {
        "name": "ColdBridge AI API",
        "version": "1.1.0",
        "maps_platform": "OpenStreetMap + Leaflet.js",
        "docs_url": "/docs",
        "health_url": f"{API_V1_PREFIX}/health"
    }
