# ColdBridge AI – Part 4 of 4: Phase 2, Final Hardening and Utility Prompts

**Steps in this file:** P0, M7, M8-B, M9, DEMO, U1–U4
**Before you start:** The Phase 1 gate in Part 3 **passed**. If it did not, go back and fix it first.
**When this part is done:** Phase 2 features work, tests pass, and the demo script is ready.

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

# PHASE 2 – Extended features

## Step 11: M7 – Inventory, surplus marketplace and buyer orders

**Run:** paste the prompt below as a **new Antigravity task**, after pasting P0.

```text
Implement only M7 (Phase 2). Start ONLY if the Phase 1 core workflow (login, batch, matching, booking) works end to end. If it does not, stop and tell me.

- Database: create the Phase 2 tables (buyer_profiles, inventory, buyer_listings, purchase_orders, alerts) with a NEW Alembic migration now, not earlier. Add the buyer demo account to the seed script.
- Inventory: create the inventory record when produce is received (booking state PRODUCE_RECEIVED), linked to the batch and booking, with quantity traceability and an audit trail for partial quantity changes.

- No payment gateway and no payment step: buyer orders are order requests only. Do not create payment tables, endpoints or screens.
- Surplus recovery: when inventory reaches the configured review deadline, create an alert and prompt the operator. The operator must approve quality BEFORE a listing can be published (unapproved items can never be published). Sliding discount (configurable) reduces the sale price over time. State that time alone does not prove food safety.
- POST/GET /api/v1/marketplace/listings and POST /marketplace/orders. Orders check remaining quantity inside a transaction so two buyers cannot buy the same stock; reject quantities above the listing.
- Buyer pages: Marketplace (filters by crop, quantity, price, location shown on a Google Map or a list; show data source and data status labels separately), My Orders. Verify order ownership on the backend.
- Tests: unapproved listing blocked, over-quantity order rejected, concurrent orders, discount calculation.

Stop after M7.
```

**Test before moving on:** inventory is created when produce is received; an unapproved surplus item can never be published; a buyer cannot order more than the listing; two buyers cannot take the same stock. There is no payment step.

**Then:** commit to Git (`git add . && git commit -m "M7 done"`).

---

## Step 12: M8B – Forecast, audit log screen and Hindi/Marathi

**Run:** paste the prompt below as a **new Antigravity task**, after pasting P0.

```text
Implement only M8 Part B (Phase 2). Start ONLY if M7 works.

- If a forecast table is needed, create it with a NEW Alembic migration.
- Baseline demand forecast screen: seasonal/rule-based estimate by crop and district. Label it "Demo forecast" or "Rule-based estimate", show the horizon, last updated time and data source. Do NOT show confidence percentages or imply a trained model.
- Admin audit log screen (reads the audit records created in M6/M7).
- Hindi/Marathi labels for the farmer screens (a simple translation file; English stays the default).

Stop after M8 Part B.
```

**Test before moving on:** the forecast is labelled as a demo/rule-based estimate; the admin audit log screen lists records; farmer screens can show Hindi/Marathi labels.

**Then:** commit to Git (`git add . && git commit -m "M8B done"`).

---

# FINAL

## Step 13: M9 – Security, tests, fallback and README

**Run:** paste the prompt below as a **new Antigravity task**, after pasting P0.

```text
Implement only M9: hardening.

1. Security review: authentication on every private endpoint; role checks and ownership checks (batches, assets, bookings, orders) enforced on the BACKEND; input validation; CORS limited to FRONTEND_ORIGIN; rate limits; secure password hashing and no plain-text passwords; JWT secret only in .env with sensible expiry; HttpOnly/Secure/SameSite cookie settings and CSRF protection; confirm the frontend never reads, stores or attaches the JWT (search for localStorage, sessionStorage and Authorization) and that every request uses credentials: 'include'; working logout; refresh tokens (if any) rotated and revocable; no secrets in code or Git history; no API keys in logs. Search the whole repository and report every place a Google key, JWT secret or database credential appears; the server key and secrets must appear only in .env.
2. Google Maps safety and cost: confirm the browser key is only in config.js, restricted by website referrer and permitted APIs; confirm the server key is restricted by permitted APIs and server environment; confirm only required APIs are enabled; confirm caching, the per-request call cap and MAX_ROUTE_CALLS_PER_DAY work; document the quotas, budget alerts and usage monitoring I must configure; remind me to verify current Google pricing, billing and free usage on official pages (no assumed free allowance, no promise the app is free to run).
3. Resilience: if Google Maps fails to load or Routes fails, the farmer can still view batches and bookings; show the list fallback and the ESTIMATED label. Add an "offline demo mode" that uses saved demo data.
4. Tests: run unit, API and scenario tests; add the missing ones (permissions, ownership, login/logout/token expiry, capacity race, SRI crop scenarios, solar fallback eligibility, route fallback, label separation, and surplus approval if Phase 2 is built). Report coverage gaps.
5. Documentation: README with setup, environment variables, seed data, run commands, demo accounts, Google Cloud setup steps, test commands and a troubleshooting section.
6. Fix issues you find (list them first and wait for my approval if a fix is large).

Confirm the SRI and solar fallback are described everywhere as a rule-based prototype and a simplified simulation, and that no hardware code was added. Return a checklist of the Definition of Done with pass/fail for each item, separately for Phase 1 and Phase 2. Stop after M9.
```

**Test before moving on:** all tests pass; no secret appears in the repository; the app works with Google Maps off (list fallback, ESTIMATED routes); the README setup works on a clean machine.

**Then:** commit to Git (`git add . && git commit -m "M9 done"`).

---

## Step 14: DEMO – Demo scenario and script

**Run:** paste the prompt below as a **new Antigravity task**, after pasting P0.

```text
Prepare the final demonstration. Do not add new features.

1. Make the demo data fixed and repeatable with one command (reset + seed).
2. CORE DEMO (Phase 1, must work): verify these scenarios: (a) normal static match, (b) urgent farmgate pickup by a van, (c) nearest is not best, (d) low sunlight changes the winner (simulation).
3. OPTIONAL PHASE 2 EXTENSION (only if M7 is built and tested): (e) near-expiry recovery to a buyer. If Phase 2 is not finished, the demo must still end cleanly at the booking.
4. Write docs/DEMO_SCRIPT.md: a 7-minute core script with exact accounts, clicks and what to say, in this order: problem, farmer login, add 500 kg mango batch with the Google Maps picker, SRI badge and reasons (say: rule-based prototype estimate), matching map and bids with route source labels, three-way comparison and "Why this match?", solar toggle (say: simplified simulation), accept offer and booking, honesty statement about simulated data and the later hardware phase. Add the optional Phase 2 extension as a separate, clearly marked section: inventory, surplus listing, buyer order.
5. Write docs/JUDGE_QA.md with answers to likely questions (AI claims, SRI limits, solar simulation limits, data, differentiation, Google Maps use and cost, capacity safety, security, payments (none in the prototype), revenue).
6. Verify the core demo runs end to end with Wi-Fi off using offline demo mode (list fallback, ESTIMATED routes).
7. Report anything that could embarrass us on stage, including any label that could be mistaken for live data.
```

**Test before moving on:** the core demo runs in about 7 minutes with Wi-Fi off; `docs/DEMO_SCRIPT.md` and `docs/JUDGE_QA.md` exist.

**Then:** commit to Git (`git add . && git commit -m "DEMO done"`).

---

# UTILITY PROMPTS (use any time)

## U1 – Fix a bug
Fill in the square brackets with your own details before pasting.

```text
Bug report. Do not change unrelated code.
What I did: [steps]
What I expected: [expected]
What happened: [exact error message or screenshot description]
Browser/OS: [info]
First find the root cause by inspecting the relevant files and logs, explain it in simple words, propose the smallest fix, apply it, add a test that would have caught it, run all tests and report.
```

## U2 – Review the last milestone

```text
Review the work of the last milestone like a strict code reviewer. Check: matches the specification and API contracts; roles and ownership enforced on the backend; business logic in services (not in JavaScript); simulated values labelled; Google keys handled correctly; tests cover success AND failure; existing features preserved. List problems by severity and fix only the critical and high ones after telling me the plan.
```

## U3 – Resume in a new chat
Paste P0 first, then this.

```text
[Paste P0 first.] We are continuing the project. Inspect the repository and README, then summarise: which milestones are complete, what is working, what is broken, and what the next milestone should be. Do not change files until I approve.
```

## U4 – Google key and cost audit

```text
Audit the repository for Google Maps key safety and cost. Report: every file containing a key or key-like string; whether the server key can reach the browser; whether the browser key is restricted by website referrer and permitted APIs and the server key by permitted APIs and server environment (tell me what I must check in Google Cloud); which Google APIs the code uses versus which I should have enabled (only the required ones); whether any Google call happens inside a loop without caching; the cache TTL, the per-request cap and the daily cap; any endpoint that lets a user trigger unlimited Google calls; and whether a list-based fallback exists when Google is unavailable. Remind me to verify current pricing, billing, quotas and free usage on official Google pages; do not state prices or assume a free allowance. Propose fixes, then apply the ones I approve.
```
