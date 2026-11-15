# ColdBridge AI – Part 1 of 4: Setup and Foundation

**Steps in this file:** P0, M0, M1, M2, M3
**Before you start:** Open your empty `ColdBridge_AI` folder in Antigravity and put your two Word documents (or their text as .md) in a `docs/` folder.
**When this part is done:** the backend runs, users can log in securely, and farmers and operators can save batches and assets. Then open Part 2.

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

## M0 – Repository audit and plan

**Run:** right after P0. No code is written.

```text
Milestone M0 only. Do NOT write or change application code yet.

1. Inspect the current repository (it may be empty). Report the existing structure, stack and anything already working.
2. Compare it with the specification and list the gaps.
3. Propose the target architecture and folder layout (frontend/, backend/app/{core,db,models,schemas,routers,services,seed}, tests/, README.md).
4. Produce a sitemap and role-based navigation for Farmer, Static Operator, Van Operator, Buyer and Admin.
5. Give a milestone plan M1-M9 plus LM1-LM3 (Leaflet & OpenStreetMap) with the files each will create, and list which database tables belong to Phase 1 and which to Phase 2 (Phase 2 tables are added later by new migrations).
6. Mark Phase 1 (core MVP: login and roles, batches, room/van registration, Leaflet/OpenStreetMap picker and asset map, rule-based SRI, matching, reverse auction ranking, solar fallback simulation, three-way comparison, safe booking) versus Phase 2 (inventory, surplus listing review, buyer marketplace and orders, demand forecast, Hindi/Marathi, admin audit log screen). The prototype has no payment gateway or payment step. State that Phase 2 starts only after the Phase 1 workflow works.
7. List risks, assumptions and decisions you need from me (for example SQLite vs PostgreSQL, language support).

Return sections A-G and wait for approval.
```

**Test before moving on:** you have a written plan and a Phase 1 vs Phase 2 table list, and no code changed. Correct anything wrong, then approve.

---

## Step 1: M1 – Backend foundation and Phase 1 database

**Run:** paste the prompt below as a **new Antigravity task**, after pasting P0.

```text
Implement only Milestone M1: foundation.

Build:
- backend/app/main.py with FastAPI, CORS limited to FRONTEND_ORIGIN, and GET /api/v1/health.
- core/config.py using pydantic-settings reading .env. Variables: APP_ENV, DATABASE_URL, JWT_SECRET, ACCESS_TOKEN_EXPIRE_MINUTES, COOKIE_SECURE, COOKIE_SAMESITE, FRONTEND_ORIGIN, OSRM_ROUTING_URL, OSM_USER_AGENT, ROUTE_CACHE_MINUTES, MAX_ROUTE_CALLS_PER_REQUEST, MAX_ROUTE_CALLS_PER_DAY, LOCATION_FRESHNESS_MINUTES.
- db/session.py and db/base.py with SQLAlchemy (SQLite default, PostgreSQL-ready).
- SQLAlchemy models with UUID primary keys, created_at/updated_at (UTC) for the PHASE 1 TABLES ONLY: users, farmer_profiles, operator_profiles, produce_batches, cold_assets, static_asset_details, mobile_asset_details (vehicle_ref, service_radius_km, solar_reliability as a simulation input, last_location_at; NO battery_state), asset_availability, spoilage_assessments, matching_requests, bids, bookings, route_cache, audit_logs. Do NOT create Phase 2 tables (buyer_profiles, inventory, buyer_listings, purchase_orders, alerts, any forecast table) or hardware tables (asset_telemetry). They are added later with NEW Alembic migrations (M7, M8 Part B, hardware phase). Do not build Phase 2 features, endpoints or screens in this milestone.
- Store locations as latitude and longitude columns (no PostGIS needed).
- Add a data_source field (LIVE or SIMULATED) to seeded business records. Data status (FRESH, STALE, UNAVAILABLE) is calculated from timestamps and the freshness limits in config; do not store it by hand. Route source (OSRM_ROUTES or ESTIMATED) is a separate field on route results.
- Alembic configured with the first migration covering the Phase 1 tables only.
- seed/demo_data.py: a repeatable script (running it twice gives the same data) that inserts demo data in Maharashtra labelled SIMULATED: 5 farmers, 6 static cold rooms, 4 mobile vans (different solar_reliability values), 12 produce batches across crops, and 2-4 bids per request, designed so that nearest, cheapest and ColdBridge picks differ.
- requirements.txt, .env.example, .gitignore (must ignore .env and *.db), and a README with setup commands for Windows CMD, PowerShell and Mac/Linux.
- Basic pytest test for /health.

Do not build auth, screens, matching or map features yet. Run the server and tests and report results. Stop after M1.
```

**Test before moving on:** server starts, `http://127.0.0.1:8000/docs` opens, `/api/v1/health` returns OK, tests pass, running the seed script twice gives the same data.

**Then:** commit to Git (`git add . && git commit -m "M1 done"`).

---

## Step 2: M2 – Secure login, roles and profiles

**Run:** paste the prompt below as a **new Antigravity task**, after pasting P0.

```text
Implement only Milestone M2: authentication and roles.

Build:
- POST /api/v1/auth/register, POST /api/v1/auth/login, GET /api/v1/auth/me and POST /api/v1/auth/logout.
- Password hashing with a recognised algorithm (bcrypt via passlib, or argon2). Never store or log plain-text passwords; never return them in responses.
- JWT with the secret read only from .env (JWT_SECRET), a short configurable expiry (ACCESS_TOKEN_EXPIRE_MINUTES), user id and role claims, and signature + expiry verified on every request.
- Browser sessions (ONE method only): on login the backend sets the JWT in an HttpOnly cookie (Secure=true in production over HTTPS; SameSite=Lax, or SameSite=None with Secure if frontend and backend are on different sites). JavaScript must NEVER read, store or manually attach the JWT: no localStorage, no sessionStorage, no JS variable, no Authorization header. Every frontend fetch uses credentials: 'include'. CORS allows only FRONTEND_ORIGIN with credentials enabled. Add CSRF protection for state-changing requests: SameSite plus a custom header (for example X-Requested-With) that api.js adds and the backend checks; this header is not the JWT.
- Logout clears the cookie. Refresh tokens are optional; if you implement them: rotation, longer expiry, hashed storage, revocation on logout.
- Reusable ownership-check helpers for batches, assets, bookings and orders, to be used by later milestones. Frontend role checks only control navigation; the backend is the real protection.
- Roles: FARMER, STATIC_OPERATOR, VAN_OPERATOR, BUYER, ADMIN.
- Reusable dependencies: get_current_user (reads the JWT from the HttpOnly cookie, verifies signature and expiry, loads the user) and require_role(...).
- Profile endpoints for farmer and operator. The BUYER role value may exist, but buyer profiles, screens and the buyer demo account are Phase 2 (M7).
- Demo accounts created by the seed script (one per Phase 1 role: farmer, static operator, van operator, admin) with documented demo passwords in the README (demo only).
- Frontend: index.html with login/register; js/api.js (one shared fetch wrapper that always uses credentials: 'include', adds the CSRF header and handles errors; it never touches the JWT); js/auth.js (calls POST /auth/login and POST /auth/logout, then calls GET /auth/me and redirects by the role it returns; it does not read, store or attach any token); role-based navigation shell for each role. Frontend role checks only control menus; the backend is the real protection.
- Rate-limit login attempts.
- Tests: a farmer cannot call an operator-only endpoint; invalid login fails; token expiry works; a tampered or expired token is rejected; logout clears the cookie; the login response sets an HttpOnly cookie and the JWT is not in the response body; a protected endpoint works with the cookie and fails without it; cookie flags are set; a search of the frontend finds no localStorage/sessionStorage/Authorization handling of a JWT; passwords never appear in responses or logs; ownership helper rejects another user's resource.

Do not build batches, assets or maps yet. Stop after M2 and report.
```

**Test before moving on:** register, login and logout work; the JWT is only in an HttpOnly cookie (check DevTools, not localStorage); a farmer cannot open operator-only routes; tests pass.

**Then:** commit to Git (`git add . && git commit -m "M2 done"`).

---

## Step 3: M3 – Produce batches and asset registration

**Run:** paste the prompt below as a **new Antigravity task**, after pasting P0.

```text
Implement only Milestone M3: farmer produce batches and operator assets (no map features yet; use simple latitude/longitude number inputs for now, the Leaflet + OpenStreetMap pickers come in LM1/LM2).

Backend:
- POST/GET /api/v1/produce/batches and GET /produce/batches/{id}. Fields: crop_code, quantity_kg, harvest_at (UTC), ambient_temp_c, latitude, longitude, notes. Validate: quantity > 0 and within a limit, valid coordinates, harvest_at not in the future.
- POST/GET/PATCH /api/v1/assets and PATCH /assets/{id}/availability. Static asset fields: supported crops, min/max temperature. Mobile asset fields: service_radius_km, solar_reliability (0-1, a SIMULATION input), last_location_at. Do NOT add battery_state or any battery, power or Peltier field in Phase 1; real battery and cooling telemetry belongs to the later hardware phase. Available capacity can never exceed total capacity or go below zero.
- Ownership checks: a farmer sees only their batches; an operator edits only their assets; others get 403/404.
- Pagination on list endpoints.

Frontend:
- farmer.html: Overview, Add Produce, My Batches with loading/empty/error/success states.
- operator.html: My Assets list, add static room, add van, update availability.
- All data access through js/api.js.
- Asset cards show data source (SIMULATED or LIVE) and data status (FRESH, STALE or UNAVAILABLE) as separate labels. A van's data status is calculated from last_location_at against LOCATION_FRESHNESS_MINUTES.

Tests: valid and invalid batch input, ownership, capacity rules. Stop after M3.
```

**Test before moving on:** a farmer can add a batch; operators can add rooms and vans; one user cannot edit another user's asset; invalid quantities are rejected.

**Then:** commit to Git (`git add . && git commit -m "M3 done"`).

---

**Next:** open `ColdBridge_Part2_Google_Maps_and_SRI.md`.
