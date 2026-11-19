# ColdBridge AI – Pay-per-Use Cold-Chain Logistics & Aggregation Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-100%20Passed-brightgreen.svg)]()
[![Maps](https://img.shields.io/badge/Maps-OpenStreetMap%20%2B%20Leaflet-orange.svg)]()
[![API%20Keys](https://img.shields.io/badge/API%20Keys-Zero%20Required-success.svg)]()

ColdBridge AI is an intelligent, pay-per-use agricultural cold-chain logistics and cross-asset aggregation platform developed for the **Avishkar Research Convention**. It connects smallholder farmers with distributed third-party static cold rooms and mobile solar refrigerated cooling vans to eliminate post-harvest agricultural losses across rural Maharashtra, India.

---

## ⚡ Quick Start: How to Run the Project (Immediate 1-Command Startup)

The fastest way to launch the entire platform (Backend API + Interactive Frontend UI + Maps) in a single command:

### 1. Windows PowerShell
```powershell
# From the ColdBridgeAI project directory:
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Windows Command Prompt (CMD)
```cmd
.\.venv\Scripts\activate.bat
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Linux / macOS
```bash
source .venv/bin/activate
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 🌐 Access Points
* **Main Landing Page:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
* **Sign In & Demo Portal:** [http://127.0.0.1:8000/login.html](http://127.0.0.1:8000/login.html)
* **Interactive API Documentation (Swagger):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **System Health Check:** [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

*(Optional Dual-Server Mode: If you prefer serving frontend files on port 5500, run `python -m http.server 5500 --bind 127.0.0.1` inside `frontend/`)*.

---

## 👥 Pre-Seeded Maharashtra Demo Accounts

The database comes pre-seeded with a deterministic benchmark dataset for the Maharashtra agricultural corridor (Nashik, Pune, Ratnagiri, Mumbai):

| Role / Operator | Demo Email | Password | Primary Hub | Access Portal |
| :--- | :--- | :--- | :--- | :--- |
| **🧑‍🌾 Smallholder Farmer** | `farmer.demo@coldbridge.ai` | `FarmerDemo123!` | Nashik, MH | `frontend/farmer.html` |
| **🏭 Static Storage Operator** | `static.demo@coldbridge.ai` | `StaticDemo123!` | Nashik, MH | `frontend/storage_operator.html` |
| **🚐 Mobile Solar Van Operator**| `van.demo@coldbridge.ai` | `VanDemo123!` | Nashik, MH | `frontend/van_operator.html` |
| **🛒 Produce Buyer (Wholesaler)** | `buyer.demo@coldbridge.ai` | `BuyerDemo123!` | Pune, MH | `frontend/buyer.html` |

> [!TIP]
> On the [login.html](http://127.0.0.1:8000/login.html) page, click any of the 4 **Quick Demo Login** buttons to automatically fill credentials and sign in instantly.

---

## 📄 Master Avishkar Documentation & Speech Files

We have generated two master Word documents (`.docx`) in the `docs/` folder specifically for the Avishkar competition and judge evaluations:

1. **[docs/ColdBridge_AI_Complete_Project_Guide_and_Avishkar_Speech.docx](docs/ColdBridge_AI_Complete_Project_Guide_and_Avishkar_Speech.docx)**
   * Complete layman explanation of the rural problem, post-harvest losses, and the solution.
   * Step-by-step user journeys for all 4 operators (Farmer, Storage Operator, Van Operator, Produce Buyer).
   * Scientific explanation of the Spoilage Risk Index (SRI) and reverse-auction matching.
   * **Ready-to-deliver presentation speeches:** 1-Minute Pitch, 3-Minute Elevator Pitch, 5-Minute Main Stage Presentation (with slide cues), and Live Demo Walkthrough.

2. **[docs/ColdBridge_AI_Avishkar_Deep_Judge_QA_Guide.docx](docs/ColdBridge_AI_Avishkar_Deep_Judge_QA_Guide.docx)**
   * 15+ comprehensive, deeply technical, and agronomic answers for university judges.
   * Covers Arrhenius Q10 decay kinetics, chilling injury in mangoes vs tomatoes, degraded solar van modeling, open-source stack justification, unit economics, food safety inspection invariants, and winning rebuttals for tough skeptic questions.

---

## 📌 Architectural Blueprint & Key Features

### 1. Cross-Asset Matching Engine
Allocates produce dynamically across both fixed physical cold rooms (Static Assets) and mobile solar-refrigerated transport vehicles (Mobile Vans).

### 2. Spoilage Risk Index (SRI)
A biophysical, rule-based heuristic calculating crop urgency (0–100) based on crop perishability, field ambient temperature, and post-harvest elapsed time:
* **0–39 (LOW):** Fresh, safe for standard transit.
* **40–69 (MEDIUM):** Needs pre-cooling within 8 hours.
* **70–100 (CRITICAL):** Rapid degradation; top dispatch priority.

### 3. Reverse-Auction Optimization
Multi-variable scoring function balancing:
$$\text{Score} = w_1(1 - \text{Dist}) + w_2(1 - \text{Price}) + w_3(\text{Solar Reliability}) + w_4(\text{Rating}) + w_5(\text{Capacity})$$

### 4. Degraded Solar Simulation
Simulates reduced refrigeration capacity during cloudy/monsoon conditions:
$$\text{Effective Capacity} = \text{Available Capacity} \times \text{Solar Reliability}$$

### 5. Near-Expiry Surplus Produce Marketplace
Rescues at-risk produce by listing inspected batches at dynamic time-decay sliding discounts (10% to 35% off wholesale).

### 6. Trilingual Rural Localization
Fully translated interfaces in **English**, **Hindi (हिंदी)**, and **Marathi (मराठी)** with instant live switching.

### 7. Zero API Keys / Zero External Cloud Costs
Built with 100% open-source software:
* **No Google Maps API Key:** Uses Leaflet 1.9.4 (vendored locally) + OpenStreetMap + Project OSRM open routing.
* **No AI/LLM API Key:** Deterministic Arrhenius kinetics and heuristic math running locally on CPU.
* **No Payment Gateway Key:** Simulated prototype transactions.

---

## 🏬 Public Cold Storage Directory (Nashik & Pune)

ColdBridge AI includes a separate, read-only directory of 10 real commercial cold storage facilities in Nashik and Pune:
* Sourced from verified public agricultural listings.
* Provides public business names, commercial addresses, and public trade phone numbers.
* **Read-Only Invariant:** Directory listings never participate in matching, bidding, or active bookings.
* To seed/update: `python -m backend.app.seed.public_directory`

---

## 🛠️ Complete Environment Setup & Migrations

If setting up from scratch on a new machine:

```powershell
# 1. Clone repository
git clone https://github.com/your-username/ColdBridgeAI.git
cd ColdBridgeAI

# 2. Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # (On Linux: source .venv/bin/activate)

# 3. Install dependencies
pip install -r backend/requirements.txt
pip install python-docx

# 4. Initialize environment file
copy backend\.env.example backend\.env

# 5. Run Alembic database migrations
python -m alembic -c backend/alembic.ini upgrade head

# 6. Seed demo dataset & public directory
python backend/app/seed/demo_data.py
python -m backend.app.seed.public_directory

# 7. Run automated test suite (100 passed)
pytest tests -v
```

---

## 🧪 Automated Test Suite (100% Pass Rate)

Run the full pytest suite:
```powershell
pytest tests -v
```
Output:
```text
================ 100 passed, 357 warnings in 174.88s (0:02:54) ================
```
Tests cover:
* Authentication & RBAC security checks (`test_auth.py`, `test_c6_security.py`).
* Matching engine & reverse-auction scoring (`test_matching.py`, `test_matching_c1.py`).
* Spoilage Risk Index formulas (`test_sri.py`, `test_sri_c2.py`).
* Multi-language translation parity across English, Hindi, and Marathi (`test_i18n_parity.py`).
* Frontend quality: zero CDN calls, vendored Leaflet verification, table responsiveness (`test_frontend_quality.py`).

---

## 📱 Mobile Responsiveness & Alignment
All 4 operator portals (`farmer.html`, `storage_operator.html`, `van_operator.html`, `buyer.html`) and `login.html` are responsive across both desktop (1280px+) and mobile (390px iPhone width). Every page satisfies:
$$\text{document.documentElement.scrollWidth} - \text{clientWidth} = 0\text{px}$$
(Zero horizontal page blowout on any tab).

---

## 📜 Academic Honesty & Competition Disclaimer
1. **Prototype Disclaimer:** Current release is a functional software prototype using deterministic benchmark data for Maharashtra.
2. **Status Labels:** Every view displays status badges: `DATA SOURCE: SIMULATED`, `DATA STATUS: FRESH`, and `ROUTE SOURCE: OSRM_ROUTES` / `ESTIMATED`.
3. **Food Safety Integrity:** Time alone does not prove food safety. Physical operator inspection is strictly mandatory before surplus produce can be published to the buyer marketplace.
#   C o l d b r i d g e A I  
 