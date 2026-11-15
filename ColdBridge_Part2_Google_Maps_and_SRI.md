# ColdBridge AI – Part 2 of 4: Google Maps and Spoilage Risk Index

**Steps in this file:** P0, GM1, GM2, GM3, M4
**Before you start:** Part 1 is finished and committed. **Finish the Google Cloud setup yourself first** (Document 1, Part E): check current pricing and billing on Google's official pages, enable only the needed APIs (Maps JavaScript, Places API (New), Geocoding, Routes), create a restricted browser key and server key, set quotas and budget alerts. Put keys in `.env` and `config.js` yourself.
**When this part is done:** the Google map, address picker, road routes and SRI all work. Then open Part 3.

---

## How to use this file
- Run **one prompt at a time**, in order. Never paste several prompts together.
- Start every **new** chat or task by pasting **P0** (given below), then the step prompt.
- Read the agent's plan before approving changes. After each step: run the app, run the tests, check the "Test before moving on" line, then commit to Git.
- If something breaks, use **U1** (in Part 4) instead of starting over.
- Never paste real API keys or passwords into a prompt. Keep keys in `backend/.env` and `frontend/js/config.js`.

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
- Phase 1 (core MVP, build first): login and roles; farmer batches; static room and van registration; Google Maps location picker and asset map; rule-based SRI; cross-asset matching; reverse auction ranking; solar fallback simulation; three-way comparison; safe booking and capacity reservation.
- Phase 2 (after Phase 1 works): inventory; operator-reviewed surplus listing; buyer marketplace and orders; demand forecast; Hindi/Marathi support; admin audit log screen.
- Do not start Phase 2 until I confirm the Phase 1 workflow works end to end.

FIXED TECH STACK (do not change without my approval)
- Frontend: HTML5, CSS3, vanilla JavaScript (ES modules). No React, Vue, Node build tools or CSS frameworks.
- Backend: Python FastAPI, Pydantic, SQLAlchemy, Alembic.
- Database: SQLite for early development; must work on PostgreSQL via DATABASE_URL.
- Maps: GOOGLE MAPS PLATFORM ONLY. Maps JavaScript API, Places API (New), Geocoding API and Routes API. Do NOT use Leaflet, OpenStreetMap, Mapbox or any other map provider.
- Charts: Chart.js (only if needed).

GOOGLE MAPS RULES
- Browser key: stored in frontend/js/config.js, restricted by HTTP referrer, used only for Maps JavaScript API and Places.
- Server key: stored ONLY in backend .env as GOOGLE_MAPS_SERVER_KEY, used only by backend services for Routes and Geocoding. Never send it to the browser, logs or Git.
- Cache route results (default 60 minutes). Limit route calls per matching request (default 8). If Google fails, use a straight-line estimate labelled ESTIMATED and keep the app working.
- Check the current official Google documentation for API usage; if something is deprecated or differs from these instructions, tell me before substituting.
- Before using any Google API, remind me to verify current official pricing, billing requirements, quotas and free usage. Never assume a fixed free allowance, never quote prices from memory and never say the app is free to operate. Enable only the APIs the app needs. Provide a list-based fallback if Google Maps is unavailable.

HONESTY RULES
- First release is a software-only prototype with deterministic demo data (Maharashtra, India: Nashik, Pune, Ratnagiri, Mumbai; currency INR).
- Use three INDEPENDENT label groups. DATA SOURCE: LIVE (from a real connected source) or SIMULATED (generated for demo/testing). DATA STATUS: FRESH (within its freshness period), STALE (older than the permitted period) or UNAVAILABLE (could not be obtained). ROUTE SOURCE: GOOGLE_ROUTES (returned by Google Routes) or ESTIMATED (approximate fallback). Show them separately, e.g. SIMULATED + FRESH, LIVE + STALE, GOOGLE_ROUTES, ESTIMATED. Never label simulated data as live. Never show an ESTIMATED route as a confirmed Google road route.
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

## Step 4: GM1 – Google Maps module and location picker

**Run:** paste the prompt below as a **new Antigravity task**, after pasting P0.

```text
Implement only GM1: the reusable Google Maps module and the location picker. Use Google Maps Platform only.

COST PRECAUTION (do this first): tell me which Google APIs this milestone needs (Maps JavaScript API and Places API (New) for the browser key) and remind me to verify current pricing, billing requirements, quotas and free usage on the official Google Maps Platform pages. Do not assume a fixed free allowance or quote prices. Enable only the required APIs. Avoid unnecessary requests: load the script once, debounce address search, and never re-search on every map movement.

Create frontend/js/maps.js (ES module) and frontend/js/config.js (GOOGLE_MAPS_BROWSER_KEY, GOOGLE_MAP_ID, DEFAULT_CENTER = Nashik, Maharashtra, DEFAULT_ZOOM). config.js must contain placeholders and a comment that the key is restricted by HTTP referrer.

maps.js must:
- Load the Maps JavaScript API once using Google's official dynamic library loader (importLibrary for "maps", "marker", "places", "geometry"), using the Map ID so Advanced Markers work.
- Export initMap(elementId, options), createMarker({lat, lng, type, title, sourceLabel}), openInfoWindow(marker, html), clearMarkers(), fitToMarkers(), and drawRoute(encodedPolyline).
- Export mountLocationPicker(containerId, onChange): a Places autocomplete search box (Places API New), a draggable marker, click-on-map to set the location, and a "Use my location" button. onChange receives {lat, lng, address}. Show the readable address when available (reverse geocode through the backend GET /api/v1/maps/reverse-geocode if you create it; otherwise skip the address).
- Handle failure: if the script fails to load, billing is missing or the key is rejected, show a clear message and a fallback manual latitude/longitude form. Never leave a blank grey box.
- Escape all user-supplied text placed in info windows (prevent XSS).

Integrate the picker into the Farmer "Add Produce" form (replace manual lat/lng inputs but keep them as a visible fallback) and into the operator "Add asset" forms.

Tests/checks: describe a manual test for each failure case and verify no API key appears anywhere except config.js (browser key only). Do not build the network map or routing yet. Stop after GM1 and tell me exactly which Google Cloud settings I must have in place: required APIs, browser-key referrer and API restrictions, quotas, budget alerts and usage monitoring.
```

**Test before moving on:** the map loads with your browser key; you can search an address and drag the pin; with a wrong key a clear message and a manual latitude/longitude form appear (no blank grey box).

**Then:** commit to Git (`git add . && git commit -m "GM1 done"`).

---

## Step 5: GM2 – Asset network map

**Run:** paste the prompt below as a **new Antigravity task**, after pasting P0.

```text
Implement only GM2: the asset network map using the maps.js module from GM1.

Build:
- Farmer "Find Cooling" page and Admin map: one Google Map showing all active assets from GET /api/v1/assets.
- Distinct markers: static cold rooms (green, label "Room") and mobile vans (blue, label "Van"). Never rely on colour alone; include text in the marker title and info window.
- Clicking a marker opens an info window: name, type, available capacity (kg), price per kg/day, solar reliability for vans, data source (SIMULATED or LIVE) and data status (FRESH, STALE or UNAVAILABLE) as separate labels.
- Filters: asset type, minimum available capacity, maximum price, status. Filters update markers without reloading the page.
- Show the farmer's batch location as a distinct marker.
- Calculate each van's data status from last_location_at: FRESH within LOCATION_FRESHNESS_MINUTES, STALE if older, UNAVAILABLE if missing. Never merge this with the data source label.
- Fallback: if the map cannot load (script error, billing, quota or key problem, or no internet), show the same assets as a sortable table.
- Cost: load assets once per filter change, make no Google calls inside marker loops, and make no Routes API calls in this milestone.
- Responsive layout: map above list on mobile, side by side on desktop.

Do not call the Routes API yet. Run through a manual test and report. Stop after GM2.
```

**Test before moving on:** rooms (green) and vans (blue) appear with info windows; filters work; each asset shows data source and data status separately; the table fallback works.

**Then:** commit to Git (`git add . && git commit -m "GM2 done"`).

---

## Step 6: GM3 – Google Routes: distance, time and route lines

**Run:** paste the prompt below as a **new Antigravity task**, after pasting P0.

```text
Implement only GM3: backend Google Routes integration.

Create backend/app/services/maps_service.py:
- compute_route_matrix(origin, destinations): calls the Google Routes API computeRouteMatrix (travel mode DRIVE) using httpx and the server key from settings, with a field mask that returns only originIndex, destinationIndex, duration, distanceMeters, status and condition. Returns distance_km and duration_minutes per destination.
- compute_route(origin, destination): calls computeRoutes and returns distance_km, duration_minutes and routes.polyline.encodedPolyline.
- reverse_geocode(lat, lng): calls the Geocoding API and returns a readable address.
- haversine_km(a, b): straight-line fallback.

Rules:
- Before coding, remind me to verify current Routes API pricing, billing requirements, quotas and free usage on the official Google pages (no assumed free allowance, no prices from memory). Request only the fields in the field mask.
- Add a daily safety limit MAX_ROUTE_CALLS_PER_DAY; when it is reached, stop calling Google and return ESTIMATED results. Log call counts (never keys) so usage can be monitored.
- Cache results in the route_cache table. Round coordinates to 4 decimals for the cache key. TTL = ROUTE_CACHE_MINUTES.
- Never call Google for more than MAX_ROUTE_CALLS_PER_REQUEST destinations; pick the nearest by straight line first.
- Timeouts and retries (max 2). On any Google error, return the haversine estimate with source = "ESTIMATED" and an explanatory note; otherwise source = "GOOGLE_ROUTES". Route source is separate from data source and data status. The UI must never present an ESTIMATED route as a confirmed Google road route.
- Never log the API key or full request headers.
- Endpoints (authenticated): GET /api/v1/maps/route?batch_id=&asset_id= and GET /api/v1/maps/reverse-geocode.
- Frontend: in the map module call the route endpoint for a selected offer and draw it with drawRoute(), showing distance, minutes and the source label.

Tests: use a mocked Google response; test cache hit, cache expiry, error fallback and the call cap. Do not change the matching score yet (M5 will use these values). Stop after GM3 and report the number of Google calls made in your manual test.
```

**Test before moving on:** each candidate shows road km and minutes with a route source label (GOOGLE_ROUTES or ESTIMATED); a repeated request uses the cache; the call cap works; tests pass with a mocked Google response.

**Then:** commit to Git (`git add . && git commit -m "GM3 done"`).

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
