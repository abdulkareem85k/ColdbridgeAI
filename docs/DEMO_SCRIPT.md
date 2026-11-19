# ColdBridge AI – 7-Minute Avishkar Live Demonstration Script

**Competition:** Avishkar Research & Innovation Competition  
**Project:** ColdBridge AI – AI-Driven Pay-per-Use Cold-Chain Logistics & Aggregation Platform  
**Target Region:** Maharashtra, India (Nashik, Pune, Ratnagiri, Mumbai)  
**Total Target Time:** 7 Minutes (5 mins Core Phase 1 + 2 mins Phase 2 Surplus Extension)

---

## ⏱️ Pre-Demo Setup Checklist (1 Minute Before Going on Stage)

1. **Reset Database:**
   ```powershell
   python backend/app/seed/demo_data.py
   ```
   *(Confirmed: Deterministic benchmark data restored).*
2. **Start Backend Server:**
   ```powershell
   cd backend
   uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```
3. **Start Frontend Server:**
   ```powershell
   cd frontend
   python -m http.server 5500 --bind 127.0.0.1
   ```
4. **Open Browser Tabs:**
   - Tab 1: `http://127.0.0.1:5500/index.html` (Landing & Login)
   - Tab 2: `http://127.0.0.1:8000/docs` (Swagger API Docs, optional backup)

---

## 🕒 PART 1: The Core Demonstration (5 Minutes)

### Minute 0:00 – 1:00 | The Problem & The Solution Architecture
- **Screen:** `index.html` (Landing Page).
- **Presenter Spoken Dialogue:**
  > "Respected judges, every year in Maharashtra, over 25 to 30% of perishable horticulture—Alphonso mangoes in Ratnagiri, tomatoes in Nashik, and table grapes in Pune—is lost between the farmgate and the cold chain. Smallholder farmers face a harsh dilemma: static cold rooms are too far away for small harvests, while mobile refrigerated transport is inaccessible and uncoordinated.
  >
  > Enter **ColdBridge AI**. ColdBridge AI is an AI-driven, pay-per-use cold-chain aggregation platform. We connect farmers with distributed static cold storage rooms and mobile solar cooling vans through dynamic, urgency-aware reverse auction matching.
  >
  > Crucially, our architecture is 100% open-source: we use **OpenStreetMap and Leaflet.js**, eliminating costly proprietary Google Maps API licensing and billing gates."

---

### Minute 1:00 – 2:00 | Farmer Login & Harvest Batch Registration with Leaflet Location Picker
- **Action:** Click the **🧑‍🌾 Farmer** quick-login button (`farmer.demo@coldbridge.ai` / `FarmerDemo123!`). Click **Sign In**.
- **Screen:** Redirected to `farmer.html`. Shows overview with 0 high-risk batches.
- **Action:** Click **Add Produce** tab (`#tabAdd`).
- **Presenter Spoken Dialogue:**
  > "Let us log in as Ramesh Patil, a mango farmer in Nashik. Ramesh just harvested 500 kg of Kesar mangoes under a scorching ambient temperature of 33°C."
- **Form Inputs:**
  - **Crop Type:** Select `Mango (Alphonso / Kesar) [High Perishability]`.
  - **Quantity:** Enter `500` kg.
  - **Harvest Timestamp:** Defaults to current time (or 4 hours ago).
  - **Ambient Temperature:** Enter `33.0` °C.
  - **Farmgate Location Picker:** Point out the OpenStreetMap + Leaflet map widget. Click a coordinate near Nashik or drag the marker.
  - **Notes:** Enter `Early morning Kesar harvest. Needs prompt pre-cooling.`
- **Action:** Click **Register Batch & Calculate SRI**.

---

### Minute 2:00 – 2:45 | Explainable Spoilage Risk Index (SRI) & Honest Prototype Disclosure
- **Screen:** Batch registers instantly; automatically navigates to **My Batches & SRI** (`#tabBatches`).
- **Visual Cue:** Highlight the **SRI Score Badge: 72/100 (HIGH URGENCY)**.
- **Presenter Spoken Dialogue:**
  > "Immediately, our backend computes the **Spoilage Risk Index (SRI)**. For this mango batch, the SRI is **72 out of 100**, placing it in the **HIGH URGENCY** band.
  >
  > *[Honesty Disclosure]*: We state with complete transparency that our SRI is a **rule-based prototype heuristic** that weighs baseline crop shelf life, hours elapsed since harvest, and field temperature curves. It is an explainable decision-support tool, not a black-box scientifically validated spoilage predictor. Crop threshold curves require domain validation by post-harvest agricultural scientists."

---

### Minute 2:45 – 3:15 | Public Cold Storage Directory (Nashik & Pune)
- **Action:** Click the **Public Directory** tab (`#tabDirectory`).
- **Screen:** Opens the **Public Cold Storage Directory – Nashik and Pune**.
- **Presenter Spoken Dialogue:**
  > "Before Ramesh books through our automated matching engine, what if he wants to explore existing commercial facilities in his district directly?
  >
  > Here is our **Public Cold Storage Directory**.
  >
  > *[Exact Judge Statement]*: 'These are real cold storage facilities in Nashik and Pune, taken from public directories. A farmer can contact them directly. The ranking and bids in our prototype are still simulated.'
  >
  > Notice the clean separation: this directory is purely informational and read-only. These 10 facilities are public commercial listings—they are NOT ColdBridge partners and never participate in matching, operator bids, or bookings."
- **Action:**
  - Click the **Pune** district filter button: show instantaneous filtering to Pune facilities (e.g., *Jai Jinendra Cold Storage*, *Iceage Cold Storage*).
  - Click **Nashik** filter button: show Nashik facilities.
  - In the search box, enter `Bhandari` and click **Search**: displays *Bhandari Cold Storage* in Kokangaon, Niphad.
  - Point out badges: `PUBLIC LISTING` and `NOT A COLDBRIDGE PARTNER`.
  - Point out contact notice: `⚠️ Unverified – call to confirm`.
  - Click **Copy Number**: clipboard alert confirms phone copied (`9371751606`).
  - Point out the **Call** button with a validated `tel:` link.

---

### Minute 3:15 – 4:00 | Cross-Asset Matching & Three-Way Comparison ("Why this Match?")
- **Action:** Click **Find Cold Chain Match** (`btnFindMatch`).
- **Screen:** Navigates to **Cooling Matches** (`#tabMatching`). The OpenStreetMap Leaflet map renders the farm location, static cold warehouses, and mobile solar vans with driving routes.
- **Visual Cue:** Show the three bids generated:
  1. **ColdBridge Pick (Winner):** `SolarGlide Alpha` (Mobile Solar Cooling Van) – ETA: 35 min | Score: 0.297 | Price: ₹1,200.
  2. **Nearest Option:** `Nashik Agro Warehouse A` (Static Cold Room) – Distance: 5.2 km | ETA: 65 min | Score: 0.334 | Price: ₹1,000.
  3. **Cheapest Option:** `Godavari Cold Vault` (Static Cold Room) – Distance: 24.8 km | ETA: 90 min | Score: 0.444 | Price: ₹800.
- **Presenter Spoken Dialogue:**
  > "Look at our three-way comparison table. Notice how the **Nearest asset is NOT the best asset**, and the **Cheapest asset is NOT the best asset**:
  > - The nearest static room is only 5 km away, but packing and transit take 65 minutes.
  > - The cheapest room costs only ₹800, but takes 90 minutes.
  > - Because the mangoes have an SRI of 72 (HIGH URGENCY), our multi-objective reverse-auction engine prioritizes dispatch speed and farmgate pre-cooling. **SolarGlide Alpha (Mobile Van)** wins because it reaches the farmgate in just 35 minutes, arresting respiration heat before irreversible cellular degradation begins.
  > - Notice the route labels: each route is independently audited as `OSRM_ROUTES` from OpenStreetMap, with automatic straight-line fallback if offline."

---

### Minute 4:00 – 4:30 | The Degraded-Solar Fallback Scenario (What-If Sunlight Drops)
- **Presenter Spoken Dialogue:**
  > "Now, what happens if cloud cover reduces solar irradiance on the mobile cooling van? Let us demonstrate our **Degraded-Solar Fallback**."
- **Action:** Open another tab or demonstrate the simulation switch:
  - Explain: When solar reliability factor drops from 0.95 to 0.40, the van's simulated effective capacity shrinks (`1,200 kg × 0.40 = 480 kg`).
  - Because 480 kg is less than Ramesh's 500 kg batch, the mobile van becomes **ineligible**, and the engine automatically reroutes the farmer to the nearest static cold room.
  - *[Honesty Disclosure]*: We explicitly state that this solar fallback is a **simplified software simulation** of effective capacity, not physical ESP32 or battery hardware telemetry.

---

### Minute 4:30 – 5:00 | Capacity Reservation & Atomic Lock
- **Action:** Click **Accept Offer & Reserve Capacity** on `SolarGlide Alpha`.
- **Screen:** Modal confirms reservation. Status moves to `RESERVED`.
- **Presenter Spoken Dialogue:**
  > "When Ramesh clicks Accept, our backend initiates a **database transaction with atomic capacity deduction**. 500 kg is deducted from the van's available capacity with a 15-minute expiration lock, preventing double-booking or overselling.
  >
  > *[Honesty Disclosure]*: There is **zero payment processing** and **zero payment gateway integration**. Prices are purely transparent prototype estimates in Indian Rupees."

---

## 🕒 PART 2: Phase 2 Surplus Recovery & Buyer Extension (2 Minutes)

### Minute 5:00 – 6:00 | Facility Reception & Dedicated Operator Panels (Quality Sign-Off Gate)
- **Action:** Log out of Farmer and log in as **🏭 Static Room Operator** (`static.demo@coldbridge.ai` / `StaticDemo123!`).
- **Screen:** Redirected to dedicated **Storage Operator Panel** (`storage_operator.html`). Click **Inventory & Surplus** tab (`#tabSurplus`).
  *(Note: Static storage operators see static facilities and drop-off storage batches in `storage_operator.html`; mobile solar van operators manage route pickups and solar capacity in `van_operator.html`).*
- **Presenter Spoken Dialogue:**
  > "Now let us examine Phase 2: **Near-Expiry Surplus Recovery** and our **Dedicated Operator Architecture**.
  > ColdBridge AI routes static cold store operators to `storage_operator.html` (green theme) and solar van fleet managers to `van_operator.html` (blue theme).
  > When produce arrives at a cooling facility (`PRODUCE_RECEIVED`), an inventory record is automatically instantiated with shelf-life tracking.
  > Here in the Storage Operator panel, we see a batch of 800 kg hydro-cooled tomatoes nearing the end of its safe storage window. An automated alert was issued to the operator.
  >
  > *[Food Safety Invariant]*: Time alone does NOT prove food safety. Under ColdBridge AI, **an unapproved surplus item can NEVER be published to buyers**. The facility operator must physically inspect the produce."
- **Action:** In the Surplus Listings table, find the pending tomato listing. Click **Inspect & Sign Off**.
- **Action:** In the modal, select **Grade A**, enter notes: `"Firmness tested; zero fungal lesions. Cold chain intact at 4°C."` Click **Approve & Release to Buyers**.
- **Visual Cue:** Status updates to `APPROVED`.

---

### Minute 6:00 – 7:00 | Buyer Marketplace & Zero-Oversell Atomic Order Placement
- **Action:** Log out and log in as **🛒 Produce Buyer** (`buyer.demo@coldbridge.ai` / `BuyerDemo123!`).
- **Screen:** Redirected to `buyer.html`.
- **Presenter Spoken Dialogue:**
  > "Now we log in as Vikram Mehta, an agro-wholesaler in Pune.
  > In the **Surplus Marketplace**, Vikram views approved produce on our OpenStreetMap Leaflet map. Notice the **transparent sliding discount**: as produce approaches its storage deadline, the price slides smoothly from 10% to 50% off, recovering economic value that would otherwise rot in a landfill."
- **Action:** Click **Place Purchase Order** on the freshly approved tomato listing (400 kg available at 25% discount).
- **Action:** In the modal, enter Quantity: `250` kg. Select Delivery: `Buyer Self-Pickup`. Click **Confirm Order Reservation**.
- **Visual Cue:** Order confirmed (`REQUESTED`).
- **Presenter Spoken Dialogue:**
  > "Notice what happened: 250 kg was atomically reserved. If another buyer attempts to order 200 kg from the remaining 150 kg, the backend immediately rejects it with HTTP 400. Double-selling is mathematically impossible.
  > Furthermore, Vikram can switch to the **Demand Forecasts** tab to inspect regional seasonal baseline demand across Maharashtra."
- **Language Switcher Demo (Bonus 15 seconds):**
  - Switch to Farmer Portal (`farmer.html`). In the header, click the language dropdown and select **मराठी** or **हिंदी**.
  - Show instantaneous UI localization into Marathi without page reloads.

---

## 🎯 Concluding Statement for Judges
> "In summary: ColdBridge AI delivers cross-asset aggregation, explainable SRI spoilage scoring, reverse-auction allocation, degraded-solar resilience, and surplus food recovery—built on a robust, 100% open-source OpenStreetMap stack with zero proprietary billing dependencies. Thank you, and we welcome your questions!"
