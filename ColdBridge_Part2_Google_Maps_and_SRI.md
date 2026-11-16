# ColdBridge AI – Part 2 of 4: OpenStreetMap, Leaflet.js and Spoilage Risk Index

> [!NOTE]
> **Map Platform Specification:**
> This project strictly utilizes **OpenStreetMap + Leaflet.js**, Nominatim (via backend rate-limited proxy), and OSRM for all mapping, location picking, and routing. Zero Google Maps Platform or proprietary paid map APIs are used.

**Steps in this file:** P0, LM1, LM2, LM3, M4
**Before you start:** Part 1 is finished and committed. OpenStreetMap + Leaflet.js requires no paid Google Cloud setup or API keys. Free, open-source tile layer and OSRM / Nominatim services.
**When this part is done:** the Leaflet map, address picker, road routes and SRI all work. Then open Part 3.

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
- The backend is the source of truth for SRI, matching, booking and capacity. Frontend only displays and does basic validation.
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

## Step 4: LM1 – Leaflet.js module and location picker

**Run:** paste the prompt below as a **new Antigravity task**, after pasting P0.

```text
Implement only LM1: the reusable Leaflet.js + OpenStreetMap module and the location picker. Use OpenStreetMap + Leaflet.js only.

No proprietary API keys or Google Cloud billing required.

Create frontend/js/maps.js (ES module) and frontend/js/config.js (OSM_TILE_URL, OSM_ATTRIBUTION, NOMINATIM_REVERSE_URL, DEFAULT_CENTER = Nashik, Maharashtra, DEFAULT_ZOOM).

maps.js must:
- Load Leaflet.js and CSS cleanly via CDN/ESM with standard OpenStreetMap tile layer (https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png) and standard OSM attribution.
- Export initMap(elementId, options), createMarker({lat, lng, type, title, sourceLabel}), openInfoWindow(marker, html) / bindPopup, clearMarkers(), fitToMarkers(), and drawRoute(coordinates).
- Export mountLocationPicker(containerId, onChange): an address search box querying OpenStreetMap Nominatim with debounced input, a draggable Leaflet marker, click-on-map to set the location, and a "Use my location" button. onChange receives {lat, lng, address}. Show the readable address when available (reverse geocode through Nominatim or backend GET /api/v1/maps/reverse-geocode).
- Handle failure: if tile loading fails or offline, show a clear message and keep the fallback manual latitude/longitude form visible. Never leave a broken container.
- Escape all user-supplied text placed in info windows / popups (prevent XSS).

Integrate the picker into the Farmer "Add Produce" form (replace manual lat/lng inputs with the picker, keeping manual inputs as a visible fallback) and into the operator "Add asset" forms.

Tests/checks: describe a test for failure cases and verify no Google API key or paid service is used. Stop after LM1.
```

**Test before moving on:** the map loads with OpenStreetMap tiles; you can search an address and drag the pin; manual latitude/longitude inputs remain functional as a reliable fallback.

**Then:** commit to Git (`git add . && git commit -m "LM1 done"`).

---

## Step 5: LM2 – Asset network map

**Run:** paste the prompt below as a **new Antigravity task**, after pasting P0.

```text
Implement only LM2: the asset network map using the maps.js module from LM1.

Build:
- Farmer "Find Cooling" page and Admin map: one Leaflet Map showing all active assets from GET /api/v1/assets.
- Distinct markers: static cold rooms (green, label "Room") and mobile vans (blue, label "Van"). Never rely on colour alone; include text in the marker title and popup.
- Clicking a marker opens a popup: name, type, available capacity (kg), price per kg/day, solar reliability for vans, data source (SIMULATED or LIVE) and data status (FRESH, STALE or UNAVAILABLE) as separate labels.
- Filters: asset type, minimum available capacity, maximum price, status. Filters update markers without reloading the page.
- Show the farmer's batch location as a distinct marker.
- Calculate each van's data status from last_location_at: FRESH within LOCATION_FRESHNESS_MINUTES, STALE if older, UNAVAILABLE if missing. Never merge this with the data source label.
- Fallback: if the map cannot load or is offline, show the same assets as a sortable table.
- Responsive layout: map above list on mobile, side by side on desktop.

Do not call the routing API yet. Run through a test and report. Stop after LM2.
```

**Test before moving on:** rooms (green) and vans (blue) appear with popups; filters work; each asset shows data source and data status separately; the table fallback works.

**Then:** commit to Git (`git add . && git commit -m "LM2 done"`).

---

## Step 6: LM3 – OSRM & OpenStreetMap Routes: distance, time and route lines

**Run:** paste the prompt below as a **new Antigravity task**, after pasting P0.

```text
Implement only LM3: backend OSRM and OpenStreetMap routing integration.

Create backend/app/services/maps_service.py:
- compute_route_matrix(origin, destinations): calls OSRM table/matrix API (travel mode driving) using httpx and settings.OSRM_ROUTING_URL, or computes haversine fallback. Returns distance_km and duration_minutes per destination.
- compute_route(origin, destination): calls OSRM route service and returns distance_km, duration_minutes, and route coordinates / encoded polyline.
- reverse_geocode(lat, lng): calls Nominatim API with User-Agent header and returns readable address.
- haversine_km(a, b): straight-line fallback.

Rules:
- 100% Free, open-source stack. Respect OpenStreetMap Nominatim Usage Policy (max 1 request/second, descriptive User-Agent header, cache responses).
- Add a daily safety limit MAX_ROUTE_CALLS_PER_DAY; when it is reached, stop external network calls and return ESTIMATED results. Log call counts so usage can be monitored.
- Cache results in the route_cache table. Round coordinates to 4 decimals for the cache key. TTL = ROUTE_CACHE_MINUTES.
- Never call routing for more than MAX_ROUTE_CALLS_PER_REQUEST destinations; pick the nearest by straight line first.
- Timeouts and retries (max 2). On any network/service error, return the haversine estimate with source = "ESTIMATED" and an explanatory note; otherwise source = "OSRM_ROUTES". Route source is separate from data source and data status. The UI must never present an ESTIMATED route as a confirmed road route.
- Endpoints (authenticated): GET /api/v1/maps/route?batch_id=&asset_id= and GET /api/v1/maps/reverse-geocode?lat=&lng=.
- Frontend: in the map module call the route endpoint for a selected offer and draw it with drawRoute(), showing distance, minutes and the source label (OSRM_ROUTES or ESTIMATED).

Tests: use mocked routing responses; test cache hit, cache expiry, error fallback and the call cap. Stop after LM3.
```

**Test before moving on:** each candidate shows road km and minutes with a route source label (OSRM_ROUTES or ESTIMATED); a repeated request uses the cache; the call cap works; tests pass with a mocked routing response.

**Then:** commit to Git (`git add . && git commit -m "LM3 done"`).

---

## Step 7: M4 – Rule-based Spoilage Risk Index

**Run:** paste the prompt below as a **new Antigravity task**, after pasting P0.

```text
Implement only M4: the rule-based SRI prototype.

IMPORTANT: the SRI is a transparent, rule-based prototype model. It is NOT a scientifically validated AI spoilage prediction and it must never claim to predict exact spoilage time. Do not invent scientifically validated thresholds. Crop-specific thresholds are placeholders that require validation by agricultural or cold-chain experts; say so in code comments, the README and the UI.

Build:
- backend/app/services/sri_engine.py as a pure, testable function. Inputs: crop perishability category, hours since harvest, ambient temperature at collection.
- A SEPARATE configuration file (config/crops.json) holding each crop's perishability class and rule thresholds. No thresholds hard-coded in Python. Use clearly labelled TEST values until experts review them.
- Output: score 0-100, risk category HIGH/MEDIUM/LOW, factors, a list of understandable plain-English reasons, a recommended action and rule_version "prototype-1". Store the rule version with EVERY calculation.
- Safe handling of missing or invalid input: missing harvest time, harvest time in the future, negative hours, impossible temperature, unknown crop. Return a clear validation error or a "cannot assess" result; never return an invented score.
- Endpoints: POST /api/v1/sri/{batch_id}/calculate, GET /api/v1/sri/{batch_id}, GET /api/v1/sri/priority-queue (visible to operators and admin). Store every assessment in spoilage_assessments.
- UI: batch detail shows the category as TEXT plus colour, the score, the factors, the reasons, the rule version and the recommended action; admin sees a priority queue. Always show the label "Prototype estimate - not a validated spoilage prediction".

Tests (pytest): different crop types (each perishability class), temperature and time scenarios, boundary values for hours and temperature, missing/invalid inputs, determinism (same input and same config give the same output), and that the rule version is stored. Stop after M4.
```

**Test before moving on:** the batch page shows HIGH/MEDIUM/LOW with reasons, rule version and the "Prototype estimate" label; bad input gives a clear error; tests for each crop class pass.

**Then:** commit to Git (`git add . && git commit -m "M4 done"`).

---

**Next:** open `ColdBridge_Part3_Matching_Booking_and_Core_Gate.md`.
