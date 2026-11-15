# ColdBridge AI – Pay-per-Use Cold-Chain Logistics & Aggregation Platform

ColdBridge AI is an AI-driven, pay-per-use cold-chain logistics and aggregation platform developed for the Avishkar competition. It connects farmers with distributed third-party static cold rooms and mobile solar cooling vans to eliminate post-harvest agricultural losses across Maharashtra, India.

---

## 📌 Architectural Blueprint & Project Overview

### Differentiators
1. **Cross-Asset Matching:** Interoperable allocation across static cold storage rooms and mobile solar cooling vans.
2. **Urgency-Aware Allocation (SRI):** Transparent, explainable rule-based Spoilage Risk Index prioritizing vulnerable crops.
3. **Reverse-Auction Scoring:** Multi-objective scoring balancing price, road distance, travel time, reliability, and remaining capacity.
4. **Degraded-Solar Fallback:** Simulated effective capacity reduction based on sunlight availability.
5. **Near-Expiry Surplus Recovery (Phase 2):** Operator-reviewed surplus listing on an open buyer marketplace.

### Tech Stack
- **Backend:** Python 3.13, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic
- **Database:** SQLite (default local development) / PostgreSQL-ready via `DATABASE_URL`
- **Frontend:** Vanilla HTML5, CSS3, ES modules JavaScript (No React, Vue, or build bundlers)
- **Maps:** OpenStreetMap + Leaflet.js (standard OSM raster tiles, Nominatim for reverse geocoding, OSRM for road distance/routes, with straight-line Haversine fallback)

---

## 🔐 Honesty & System Disclaimers

1. **Software Prototype:** Current release is a functional software prototype using deterministic demo data for Maharashtra (Nashik, Pune, Ratnagiri, Mumbai; currency INR).
2. **Independent Status Labels:**
   - **DATA SOURCE:** `LIVE` (user-created) or `SIMULATED` (demo generated).
   - **DATA STATUS:** `FRESH` (within freshness threshold), `STALE` (exceeds threshold), or `UNAVAILABLE`.
   - **ROUTE SOURCE:** `OSRM_ROUTES` (OpenStreetMap/OSRM road route) or `ESTIMATED` (straight-line haversine fallback).
3. **Spoilage Risk Index (SRI):** Transparent rule-based prototype model; **not** a scientifically validated prediction.
4. **Solar Fallback Simulation:** Calculated as `effective_capacity = available_capacity * solar_reliability`. Real battery, power, and Peltier cooling load telemetry belong to a subsequent hardware phase.
5. **No Payment Processing:** No payment step or gateway exists in this prototype. Rates and costs are estimates in INR.

---

## 👥 Demo User Accounts (Phase 1)

All demo accounts are pre-seeded in the Maharashtra dataset:

| Role | Email | Password | Primary District |
|---|---|---|---|
| **Farmer** | `farmer.demo@coldbridge.ai` | `FarmerDemo123!` | Nashik, MH |
| **Static Room Operator** | `static.demo@coldbridge.ai` | `StaticDemo123!` | Pune, MH |
| **Mobile Van Operator** | `van.demo@coldbridge.ai` | `VanDemo123!` | Nashik, MH |
| **System Administrator** | `admin.demo@coldbridge.ai` | `AdminDemo123!` | Mumbai, MH |

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

# Run database migrations
cd backend
alembic upgrade head
cd ..

# Seed Maharashtra demo data
python backend/app/seed/demo_data.py

# Run unit & security tests
pytest -v
```

### 2. Windows Command Prompt (CMD)

```cmd
cd C:\Users\karee\Downloads\ColdBridgeAI
python -m venv .venv
.\.venv\Scripts\activate.bat
pip install -r backend\requirements.txt
copy backend\.env.example backend\.env
cd backend
alembic upgrade head
cd ..
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
cd backend
alembic upgrade head
cd ..
python backend/app/seed/demo_data.py
pytest -v
```

---

## 🏃 Running the Application

### Start Backend API Server
```powershell
# From project root with .venv active:
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- Interactive API Docs (Swagger UI): [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health Check: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

### Serve Frontend UI
In a separate terminal:
```powershell
# From project root:
cd frontend
python -m http.server 5500 --bind 127.0.0.1
```
- Open in Browser: [http://127.0.0.1:5500/index.html](http://127.0.0.1:5500/index.html)

---

## 🔒 Security Architecture
- **HttpOnly Cookies:** Authentication tokens (`access_token`) are strictly stored in HttpOnly, SameSite cookies. JavaScript code never reads, stores, or attaches JWTs.
- **CSRF Protection:** State-changing requests (`POST`, `PUT`, `PATCH`, `DELETE`) require the `X-Requested-With: XMLHttpRequest` header.
- **Role-Based Access Control:** Validated on backend endpoints using FastAPI dependencies.
- **Rate Limiting:** Prevents brute-force credential stuffing on `/api/v1/auth/login`.
