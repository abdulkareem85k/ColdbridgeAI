# ColdBridge AI – Part 3 of 4: Matching, Booking and the Phase 1 Gate

**Steps in this file:** P0, M5, M6, M8-A, Phase 1 Gate
**Before you start:** Parts 1 and 2 are finished and committed.
**When this part is done:** the full core demo passes the gate checklist below. Only then open Part 4.

---

## How to use this file
- Run **one prompt at a time**, in order. Never paste several prompts together.
- Start every **new** chat or task by pasting **P0** (given below), then the step prompt.
- Read the agent's plan before approving changes. After each step: run the app, run the tests, check the "Test before moving on" line, then commit to Git.
- If something breaks, use **U1** (in Part 4) instead of starting over.
- Keep secrets in `backend/.env` and `frontend/js/config.js`.

## P0 – Master context prompt (paste at the start of every new task)

The agent should reply "Context understood" and write no code.

```text
You are a senior full-stack engineer and software architect. You are helping me build ColdBridge AI for the Avishkar competition. The attached "ColdBridge AI Step-by-Step Implementation Guide" and the project abstract are the specification.

PROJECT
ColdBridge AI is an AI-driven, pay-per-use cold-chain logistics and aggregation platform. It connects farmers with third-party static cold rooms and mobile solar cooling vans. Core differentiators:
1. Cross-asset matching across static rooms and mobile vans.
2. Urgency-aware allocation using an explainable Spoilage Risk Index (SRI).
3. Cross-asset reverse-auction scoring (price, distance, travel time, reliability, capacity).
4. Degraded-solar fallback for mobile vans.
5. Near-expiry surplus recovery through an operator-reviewed buyer marketplace.

DEVELOPMENT PHASES
- Phase 1 (core MVP, build first): login and roles; farmer batches; static room and van registration; OpenStreetMap + Leaflet.js location picker and asset map; rule-based SRI; cross-asset matching; reverse auction ranking; solar fallback simulation; three-way comparison; safe booking and capacity reservation.
- Phase 2 (after Phase 1 works): inventory; operator-reviewed surplus listing; buyer marketplace and orders; demand forecast; Hindi/Marathi support; admin audit log screen.
- Do not start Phase 2 until I confirm the Phase 1 workflow works end to end.

FIXED TECH STACK (do not change without my approval)
- Frontend: HTML5, CSS3, vanilla JavaScript (ES modules). No React, Vue, Node build tools or CSS frameworks.
- Backend: Python FastAPI, Pydantic, SQLAlchemy, Alembic.
- Database: SQLite for early development; must work on PostgreSQL via DATABASE_URL.
- Maps: OPENSTREETMAP + LEAFLET.JS ONLY. Leaflet.js (ES modules / lightweight CDN) with OpenStreetMap standard tiles and Nominatim / OSRM for geocoding and routing fallback. Do NOT use Google Maps Platform, Mapbox or proprietary paid map providers.
- Charts: Chart.js (only if needed).

OPENSTREETMAP + LEAFLET.JS RULES
- Tile Layer: OpenStreetMap standard tiles (https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png) rendered with Leaflet.js; include mandatory OpenStreetMap attribution.
- Geocoding & Routing: Use OpenStreetMap Nominatim for address search / reverse geocoding with a descriptive User-Agent, and OSRM (Open Source Routing Machine) or straight-line Haversine fallback for road routing.
- No Proprietary Keys: No Google Maps API keys or billing accounts required. Free, open-source stack.
- Cache route results (default 60 minutes). Limit route calls per matching request (default 8). If OSRM fails or times out, use a straight-line estimate labelled ESTIMATED and keep the app working.
- Respect OSM Nominatim Usage Policy (max 1 request/sec, descriptive User-Agent header, cache responses). Provide a list-based fallback if tile rendering or network is unavailable.

HONESTY RULES
- First release is a software-only prototype with deterministic demo data (Maharashtra, India: Nashik, Pune, Ratnagiri, Mumbai; currency INR).
- Use three INDEPENDENT label groups. DATA SOURCE: LIVE (from a real connected source) or SIMULATED (generated for demo/testing). DATA STATUS: FRESH (within its freshness period), STALE (older than the permitted period) or UNAVAILABLE (could not be obtained). ROUTE SOURCE: OSRM_ROUTES (returned by OpenStreetMap/OSRM) or ESTIMATED (approximate fallback). Show them separately, e.g. SIMULATED + FRESH, LIVE + STALE, OSRM_ROUTES, ESTIMATED. Never label simulated data as live. Never show an ESTIMATED route as a confirmed road route.
- The SRI is a transparent rule-based prototype, not a scientifically validated spoilage prediction. Never claim it predicts exact spoilage time and never invent validated thresholds; crop thresholds need validation by agricultural or cold-chain experts.
- The solar fallback (effective capacity = available capacity x solar reliability) is a simplified simulation. Never present it as a real battery, power, Peltier cooling load, temperature stability or operating-time calculation. Hardware (ESP32, sensors, battery monitoring, Peltier) is a later phase and is NOT part of this software MVP.
- Never claim real GPS, real sensors, validated spoilage prediction, or measured spoilage reduction.
- The prototype has NO payment step and NO payment gateway. Do not build, mock or integrate any payment processing. Prices are shown only as an estimate.

ENGINEERING RULES
- Inspect the repository before changing anything. Preserve working code. Do not delete or rewrite files without asking.
- Thin routers; business logic in services; Pydantic schemas for all requests/responses.
- The backend is the source of truth for SRI, matching, booking and capacity. Frontend only displays and basic validation.
- Role-based access control and ownership checks (batches, assets, bookings, orders) on every private endpoint, enforced on the backend. Frontend role checks are never the only protection.
- Authentication: securely hashed passwords (bcrypt/argon2), JWT secret only in backend .env, short token expiry, ONE session method: the JWT lives only in an HttpOnly cookie (Secure in production, suitable SameSite) set by the backend. JavaScript must never read, store (localStorage, sessionStorage, variables) or manually attach the JWT. Every frontend request uses credentials: 'include'. Backend dependencies verify the cookie. Logout clears it. CSRF protection for cookie-based requests.
- Use database transactions to prevent capacity overbooking.
- Clear loading, empty, error and success states. Responsive, accessible UI (labels, keyboard use, text plus colour).
- Keep secrets out of code. Commit .env.example only.
- Add tests for business-critical logic and run them.

WORKING METHOD
For each milestone: (1) inspect relevant files, (2) state your plan and the files you will change, (3) implement the smallest complete working slice, (4) run the app and tests and fix errors, (5) summarise changed files, commands run and test results, (6) list remaining issues, (7) STOP and wait for my approval.

Reply "Context understood" and wait for my next prompt.
```

---

## Step 8: M5 – Matching, reverse auction, solar fallback and comparison

**Run:** paste the prompt below as a **new Antigravity task**, after pasting P0.

```text
Implement only M5: the core matching engine. Use the real road distance and travel time from LM3 (maps_service).

Services: eligibility.py, matching_engine.py, auction_scoring.py, solar_adjustment.py.

1. Eligibility filters (exclude with a recorded reason): asset inactive or unavailable in the window; outside service radius; effective capacity below requested quantity; crop or temperature not supported; mobile van data status STALE or UNAVAILABLE (location older than LOCATION_FRESHNESS_MINUTES or missing).
2. Solar fallback (a SIMPLIFIED PROTOTYPE SIMULATION): effective_mobile_capacity = available_capacity_kg * solar_reliability (0-1), and a reliability penalty = 1 - solar_reliability.
   - solar_reliability is a configurable simulation input, not a measured value.
   - Changing the sunlight level must change the van's effective capacity and its matching eligibility (a van whose effective capacity is below the requested quantity is excluded with a recorded reason).
   - This does NOT calculate battery state, power consumption, Peltier cooling load, temperature stability or remaining operating time. Do not present it as a real battery or cooling-performance calculation, and do not add hardware code. Real telemetry and energy calculations belong to a later hardware phase. Say this in code comments, the README and the UI.
3. Bids: POST /api/v1/matching/requests, POST /matching/requests/{id}/bids, POST /matching/requests/{id}/rank, GET /matching/requests/{id}. Bid fields: asset_id, offered_capacity_kg, price_total, eta_minutes, valid_until, note. Support auto-simulated bids for demo assets, labelled SIMULATED.
4. Scoring (lower is better). Weights live in config/matching_weights.json and must sum to 1.0 (validate at startup): price 0.30, distance 0.15, time 0.20, reliability 0.20, capacity 0.15; urgency_bonus_max 0.15; urgency band_factor HIGH = 1.0, MEDIUM = 0.0, LOW = 0.0 (configurable).
   score = 0.30*price_n + 0.15*distance_n + 0.20*time_n + 0.20*reliability_penalty + 0.15*capacity_penalty - urgency_bonus
   Exact definitions (identical to Document 1, Section G.3). Everything is computed ONLY over the eligible offers:
   - price_n, distance_n, time_n: min-max normalisation of price_total, road distance (km) and eta_minutes: x_n = (x - min) / (max - min). 0 = best, 1 = worst. If max == min (only ONE eligible offer, or all offers equal on that metric) then x_n = 0 for every offer. Never divide by zero.
   - reliability_penalty = 1 - solar_reliability (clamped to 0..1) for a mobile van; 0 for a static room in Release 1.
   - capacity_penalty = requested_kg / effective_available_kg, where effective_available_kg = available_capacity_kg for a static room and available_capacity_kg * solar_reliability for a van. For an eligible offer it is between 0 and 1 (1.0 = would use all remaining space). It is NOT min-max normalised.
   - urgency_bonus = urgency_bonus_max * band_factor(SRI band) for a mobile van; 0 for a static room; 0 if the SRI cannot be assessed.
   - Scores can be below 0 because of the bonus; only the order matters. Rank by the UNROUNDED score ascending, display 3 decimals, and break exact ties by lower price_total, then lower eta_minutes, then asset_id. The same inputs and the same config must always give the same ranking.
   - Distance and time come from LM3 (OSRM_ROUTES, or ESTIMATED when routing is unavailable). Never mix the SRI score with monetary price; the SRI band only controls the urgency bonus. Do not make any real-world performance claims.
5. Explanation: for every offer return the score breakdown by component and 2-4 plain-English reasons.
6. Baselines on the same data: "nearest eligible" and "lowest price eligible". Return all three picks and why they differ.
7. UI: results page with ranked offers, a "Why this match?" panel (component breakdown bars plus reasons), a three-way comparison table (Nearest vs Cheapest vs ColdBridge), the route of the selected offer drawn on the Leaflet Map, a route source label (OSRM_ROUTES or ESTIMATED) on every distance/time, a visible note "Solar fallback is a simplified simulation", and an admin toggle to change a van's solar reliability and re-run ranking.

Tests: each filter; normalisation edge cases (single offer, equal values); capacity_penalty and reliability_penalty definitions; urgency bonus only for vans and only when justified; tie-breaking; and the worked example below, which must be reproduced (tolerance 0.0005):
   Requested 500 kg, SRI HIGH. A static room: Rs 1000, 5 km, 65 min, 1000 kg available. B van: Rs 1200, 8 km, 35 min, 800 kg available, solar 0.9 (effective 720 kg). C static room: Rs 800, 25 km, 90 min, 800 kg available.
   Expected: A 0.334, B 0.297 (winner), C 0.444. Nearest-only = A, cheapest-only = C, ColdBridge = B.
   Solar test: B solar 0.5 gives effective 400 kg < 500 kg, so B is excluded; scores are recalculated over A and C only: A 0.375, C 0.444, so A wins. Document the formula in README. Stop after M5.
```

**Test before moving on:** the ranking shows a score breakdown and "Why this match?"; the three-way comparison shows different picks; the worked example gives A 0.334, B 0.297 (winner), C 0.444; lowering solar reliability to 0.5 excludes the van and A wins with 0.375.

**Then:** commit to Git (`git add . && git commit -m "M5 done"`).

---

## Step 9: M6 – Safe booking and capacity reservation

**Run:** paste the prompt below as a **new Antigravity task**, after pasting P0.

```text
Implement only M6: booking and capacity safety (Phase 1). Do not build inventory, surplus or buyers here; they belong to Phase 2 (M7).

- POST /api/v1/matching/requests/{id}/allocate: farmer accepts one offer. Inside ONE database transaction: lock the asset capacity row (SELECT ... FOR UPDATE on PostgreSQL; an equivalent atomic conditional UPDATE on SQLite), re-check capacity, reserve it, create the booking, mark the winning bid accepted and expire the other bids. If capacity changed, return 409 and tell the user to re-run matching.
- Reservation expiry (default 15 minutes): a booking in RESERVED that is not confirmed becomes EXPIRED automatically and its capacity is released.
- Booking state machine (identical to Document 1, Section G.7). States: REQUESTED, MATCHED, RESERVED, CONFIRMED, PICKUP_SCHEDULED (van bookings only), PRODUCE_RECEIVED, IN_STORAGE, COMPLETED; terminal: COMPLETED, CANCELLED, EXPIRED, FAILED. Allowed transitions ONLY:
  REQUESTED -> MATCHED, CANCELLED, FAILED
  MATCHED -> RESERVED, CANCELLED, EXPIRED
  RESERVED -> CONFIRMED, CANCELLED, EXPIRED
  CONFIRMED -> PICKUP_SCHEDULED (van bookings only), PRODUCE_RECEIVED (room bookings), CANCELLED, FAILED
  PICKUP_SCHEDULED -> PRODUCE_RECEIVED, CANCELLED, FAILED
  PRODUCE_RECEIVED -> IN_STORAGE, FAILED
  IN_STORAGE -> COMPLETED, FAILED
  Reject every other transition. Record who changed the state and when.
- Capacity rules: capacity is held when the booking enters RESERVED. Release it, in the same transaction as the state change and exactly once per booking, on CANCELLED or EXPIRED (from RESERVED), on CANCELLED or FAILED (from CONFIRMED or PICKUP_SCHEDULED), on FAILED (from PRODUCE_RECEIVED) and on COMPLETED or FAILED (from IN_STORAGE). Cancellation is allowed only before PRODUCE_RECEIVED. Available capacity must never exceed total capacity.
- In Phase 1 the operator moves bookings through PRODUCE_RECEIVED, IN_STORAGE and COMPLETED as simple status changes. Do not create inventory records here (Phase 2, M7).
- Pay-per-use price estimate shown before confirmation: quantity_kg x rate_per_kg_per_day x days, plus transport and platform fee as separate line items in INR. This is an estimate only: there is no payment step or gateway.
- Audit log RECORDS for asset, bid and booking changes (no passwords or tokens). The admin audit log screen is Phase 2.
- Verify ownership on the backend: only the farmer who owns the batch can accept an offer; only the operator who owns the asset can change its bookings.
- UI: booking detail with a timeline, price breakdown and cancellation rule.

Tests: two simultaneous allocations for the same capacity (only one succeeds), every allowed and several invalid transitions (including van-only PICKUP_SCHEDULED), reservation expiry, capacity released exactly once on CANCELLED, EXPIRED and FAILED (never twice, never above total), ownership checks, audit records. Stop after M6, then run the full core demo (login, batch, matching, comparison, solar toggle, booking) before moving on.
```

**Test before moving on:** accepting an offer creates a booking; two simultaneous requests for the same capacity give one success and one conflict; invalid state changes are rejected; cancel or expiry releases capacity exactly once.

**Then:** commit to Git (`git add . && git commit -m "M6 done"`).

---

## Step 10: M8A – Dashboards and simulation controls

**Run:** paste the prompt below as a **new Antigravity task**, after pasting P0.

```text
Implement only M8 Part A: dashboards and simulation controls (Phase 1). Do not build any Phase 2 item.

- Role dashboards (farmer, operator, admin) using real API data: counts, active bookings, a priority list taken from the SRI priority queue (there is no alerts table in Phase 1), utilisation, recent activity (from audit_logs). Add Chart.js charts only where useful.
- Admin simulation controls: reset demo data, toggle a van's solar reliability (simulation input), advance a simulated clock, simulate a temperature update. Every simulated record carries data_source = "SIMULATED".
- Labels on every metric, map and value, shown as INDEPENDENT groups: data source (LIVE or SIMULATED) and data status (FRESH, STALE or UNAVAILABLE, calculated from timestamps and freshness limits). Route values also show OSRM_ROUTES or ESTIMATED. Never label simulated data as LIVE.
- Loading, empty and error states for every dashboard.

Stop after M8 Part A.
```

**Test before moving on:** dashboards show real database values; the admin can reset demo data and change solar reliability; every value shows its labels.

**Then:** commit to Git (`git add . && git commit -m "M8A done"`).

---

## PHASE 1 GATE – do not skip

Do the full **core demo** by hand. If anything fails, fix it with U1 (Part 4) before starting Phase 2.

- [ ] Log in as a farmer and add a 500 kg mango batch using the Leaflet location picker
- [ ] SRI badge shows with reasons and the prototype label
- [ ] Map shows rooms and vans; matching shows bids with route source labels
- [ ] Three-way comparison shows nearest, cheapest and ColdBridge picks
- [ ] "Why this match?" panel shows the score breakdown
- [ ] Lowering solar reliability changes the result
- [ ] Accepting an offer creates a booking and reserves capacity
- [ ] Everything still works with the map list fallback
- [ ] No API key or secret is in Git

**Next:** open `ColdBridge_Part4_Phase2_Final_and_Utility.md`.
