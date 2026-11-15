# ColdBridge AI – Pay-per-Use Cold-Chain Logistics & Aggregation Platform

ColdBridge AI is an AI-driven, pay-per-use cold-chain logistics and aggregation platform developed for the Avishkar competition. It connects smallholder farmers with distributed third-party static cold rooms and mobile solar cooling vans to eliminate post-harvest agricultural losses across Maharashtra, India.

---

## 📌 Architectural Blueprint & Project Overview

### Core Differentiators
1. **Cross-Asset Matching:** Interoperable allocation across static cold storage rooms and mobile solar cooling vans.
2. **Urgency-Aware Allocation (SRI):** Transparent, explainable rule-based Spoilage Risk Index prioritizing vulnerable crops.
3. **Reverse-Auction Scoring:** Multi-objective scoring balancing price, road distance, travel time, reliability, and remaining capacity.
4. **Degraded-Solar Fallback:** Simulated effective capacity reduction based on sunlight availability (`effective_capacity = available_capacity * solar_reliability`).
5. **Near-Expiry Surplus Recovery (Phase 2):** Operator-reviewed surplus marketplace with transparent sliding discounts and atomic order reservations.
6. **Regional Demand Forecasting (Phase 2):** Rule-based seasonal baseline demand by crop and district.
7. **Bilingual Localization (Phase 2):** English, Hindi (हिंदी), and Marathi (मराठी) localization for smallholder farmers.

### Fixed Tech Stack
- **Backend:** Python 3.10+, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic
- **Database:** SQLite (default local development) / PostgreSQL-ready via `DATABASE_URL`
- **Frontend:** Vanilla HTML5, CSS3, ES modules JavaScript (Zero React, Vue, or build bundlers)
- **Maps:** **OpenStreetMap + Leaflet.js ONLY** (standard OSM raster tiles, Nominatim for reverse geocoding, OSRM for road distance/routes, with straight-line Haversine fallback). **Zero Google Maps Platform or proprietary paid map APIs.**

---

## 🔐 Honesty & System Disclaimers

1. **Software-Only Prototype:** Current release is a functional software prototype using deterministic benchmark data for Maharashtra (Nashik, Pune, Ratnagiri, Mumbai; currency INR).
2. **Independent Status Labels:**
   - **DATA SOURCE:** `LIVE` (user-created) or `SIMULATED` (demo generated).
   - **DATA STATUS:** `FRESH` (within freshness threshold), `STALE` (exceeds threshold), or `UNAVAILABLE`.
   - **ROUTE SOURCE:** `OSRM_ROUTES` (OpenStreetMap/OSRM road route) or `ESTIMATED` (straight-line haversine fallback).
3. **Spoilage Risk Index (SRI):** Transparent rule-based prototype heuristic; **not** a scientifically validated prediction.
4. **Solar Fallback Simulation:** Calculated as `effective_capacity = available_capacity * solar_reliability`. Real battery telemetry, Peltier cooling load, and ESP32 hardware sensors belong to a subsequent physical phase.
5. **Zero Payment Gateways:** No payment step or gateway exists in this prototype. Rates and order values are prototype estimates only.
6. **Food Safety Honesty:** Time alone does not prove food safety. Physical operator inspection is strictly mandatory before surplus produce can be published to the buyer marketplace.

---

## 👥 Demo User Accounts (Pre-seeded Maharashtra Dataset)

| Role | Email | Password | Primary Location | Access Portal |
|---|---|---|---|---|
| **Farmer** | `farmer.demo@coldbridge.ai` | `FarmerDemo123!` | Nashik, MH | `frontend/farmer.html` |
| **Static Room Operator** | `static.demo@coldbridge.ai` | `StaticDemo123!` | Nashik, MH | `frontend/operator.html` |
| **Mobile Van Operator** | `van.demo@coldbridge.ai` | `VanDemo123!` | Nashik, MH | `frontend/operator.html` |
| **Produce Buyer (Wholesaler)** | `buyer.demo@coldbridge.ai` | `BuyerDemo123!` | Pune, MH | `frontend/buyer.html` |
| **System Administrator** | `admin.demo@coldbridge.ai` | `AdminDemo123!` | Mumbai, MH | `frontend/admin.html` |

---

## 🚀 Setup & Installation Instructions

### Prerequisites
- Python 3.10+ (Tested on Python 3.13)
- Git

### 1. Windows PowerShell

```powershell
# Clone or navigate to the project directory
cd C:\Users\karee\Downloads\ColdBridgeAI

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install backend dependencies
pip install -r backend/requirements.txt

# Copy environment configuration
Copy-Item backend/.env.example backend/.env

# Run database migrations (creates Phase 1 & Phase 2 tables)
python -m alembic -c backend/alembic.ini upgrade head

# Seed Maharashtra deterministic demo dataset
python backend/app/seed/demo_data.py

# Run unit, security & scenario tests (39/39 passing)
pytest -v
```

### 2. Windows Command Prompt (CMD)

```cmd
cd C:\Users\karee\Downloads\ColdBridgeAI
python -m venv .venv
.\.venv\Scripts\activate.bat
pip install -r backend\requirements.txt
copy backend\.env.example backend\.env
python -m alembic -c backend\alembic.ini upgrade head
python backend\app\seed\demo_data.py
pytest -v
```

### 3. macOS / Linux

```bash
cd ColdBridgeAI
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
python3 -m alembic -c backend/alembic.ini upgrade head
python3 backend/app/seed/demo_data.py
pytest -v
```

---

## 🏃 Running the Application

### 1. Start Backend API Server
```powershell
# From project root with .venv active:
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- Interactive API Docs (Swagger UI): [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health Check: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

### 2. Serve Frontend UI
In a separate terminal:
```powershell
# From project root:
cd frontend
python -m http.server 5500 --bind 127.0.0.1
```
- Open in Browser: [http://127.0.0.1:5500/index.html](http://127.0.0.1:5500/index.html)

---

## 🔒 Security Architecture

- **HttpOnly Cookies:** Authentication tokens (`access_token`) are strictly stored in HttpOnly, SameSite cookies. Frontend JavaScript NEVER reads, stores, or manually attaches JWTs (`credentials: 'include'` only).
- **CSRF Protection:** State-changing requests (`POST`, `PUT`, `PATCH`, `DELETE`) require the `X-Requested-With: XMLHttpRequest` header.
- **Backend Ownership Verification:** Role-based access control and strict resource ownership checks (batches, assets, bookings, inventory, orders) are enforced on the backend.
- **Atomic Concurrency Protection:** Booking capacity reservations and surplus inventory order requests execute within database transactions with row-level checks, guaranteeing zero double-selling or overselling.
- **Zero Secrets in Code:** Secrets (`JWT_SECRET`, database URLs) live exclusively in `.env`.

---

## 🗺️ OpenStreetMap & Routing Safety

- **Open-Source Attribution:** Leaflet maps render standard OpenStreetMap raster tiles with mandatory attribution: `&copy; OpenStreetMap contributors`.
- **Nominatim Usage Policy:** Reverse-geocoding requests include a descriptive User-Agent (`ColdBridgeAI/1.0 (Avishkar Competition)`).
- **Route Caching & Safety Caps:** OSRM routes are cached in the database (default 60 min TTL) with daily request capping (`MAX_ROUTE_CALLS_PER_DAY=1000`).
- **Resilient Fallback:** If network connection or OSRM is unavailable, straight-line Haversine distance and duration are automatically calculated and clearly marked as `ESTIMATED`.
- **Offline Demo Mode:** If map tiles fail to load, clean list views and coordinate presets (Nashik, Pune, Ratnagiri) allow uninterrupted offline demonstration.
