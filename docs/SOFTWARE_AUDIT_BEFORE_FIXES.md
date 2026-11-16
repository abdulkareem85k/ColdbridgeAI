# ColdBridge AI – Software Audit Before Fixes (Phase C0 Report)

**Date:** 2026-11-16  
**Auditor:** Senior Full-Stack Engineer  
**Scope:** Phase C0 Baseline Audit covering Database, Security, Matching Engine, SRI Privacy, OpenStreetMap routing, and API ownership.

---

## 1. Baseline Test Execution Results

- **Command:** `pytest -v tests/`
- **Result:** **39 Passed, 0 Failed, 0 Skipped** (in 81.85 seconds)
- **Dependency Issues:** None detected in current `.venv`.
- **Note on Test Coverage Gap:** Existing tests passed because they reused the pre-seeded bid `bd000000-0000-0000-0000-000000000002` rather than exercising end-to-end allocation of a newly created request without pre-existing bids.

---

## 2. Database Files & Integrity Audit

### Exact Database Path
- **Active DB Used by Running App:** `C:\Users\karee\Downloads\ColdBridgeAI\backend\coldbridge.db` (Size: 1,253,376 bytes).
- **Settings Source:** Defined in `backend/.env` as `DATABASE_URL=sqlite:///./coldbridge.db` and resolved relative to `backend/` working directory.

### Other `.db` Files Found in Workspace
1. `coldbridge.db` (Repository root): 0 bytes. **Stray empty artifact** created unintentionally during early development commands. Should be removed.
2. `test_coldbridge.db` (Repository root): 458,752 bytes. **Test database** created and refreshed by `tests/conftest.py` during pytest runs.
3. `backups/coldbridge_20261116_111949.db`: 1,253,376 bytes. **Timestamped backup** created during C0 audit using SQLite backup API.

### Migration & Seeding Verification on Clean Database
- Successfully ran `alembic upgrade head` and `seed_demo_data()` on a fresh temporary SQLite database (`temp_test_migration.db`).
- **Phase 1 migration:** `e9e4527d6cfb` (applied cleanly).
- **Phase 2 migration:** `f189c632803a` (applied cleanly).
- **Seed records verified:** 5 farmers, 2 operators, 1 buyer, 1 admin, 6 static cold rooms, 4 mobile vans, 12 batches, active inventory, surplus listings, and regional demand forecasts.

---

## 3. Detailed Problems Audit: Confirmed or Refuted

| ID | Issue Description | Location | Status | Proposed Fix |
|---|---|---|:---:|---|
| **A** | **Allocation 404 Bug on New Requests:** When no bid exists for an asset, engine invents fake ID `bid_id = f"auto-{asset.id[:8]}"` and never persists it. `allocate_offer_transaction` looks up `Bid` in DB, fails with 404, breaking new allocations. | `backend/app/services/matching_engine.py` (L124–135), `booking_service.py` (L95–97) | **CONFIRMED** | In `run_cross_asset_matching`, persist auto-generated bids as real `Bid` rows with `data_source="SIMULATED"`. Remove all `auto-...` ID paths. |
| **A2** | **Simulated vs Live Bid Conflation & Missing Checks:** `submit_bid` forces `data_source="SIMULATED"` for real operators; `/rank` response schema (`RankedOfferDetail`) omits `data_source`; `allocate_offer_transaction` only checks `is_expired`, not `valid_until < now`. | `backend/app/routers/matching.py` (L114), `schemas/matching.py` (L62–84), `booking_service.py` (L99) | **CONFIRMED** | Set `data_source="LIVE"` for operator-submitted bids in `submit_bid`. Expose `data_source` in `RankedOfferDetail`. Add `valid_until < now` check in `allocate_offer_transaction`. |
| **B** | **Missing Ownership on Matching Requests:** `POST /requests/{id}/rank` and `GET /requests/{id}` have zero ownership checks. Furthermore, `GET` runs matching and performs DB writes. | `backend/app/routers/matching.py` (L135–187) | **CONFIRMED** | Add `verify_matching_request_access` in `ownership_service.py` (allow owning farmer, admin, or bidding operator; 403 otherwise). Ensure `GET` is strictly read-only without state mutation. |
| **C** | **SRI Authorization & Priority Queue Privacy Leak:** `/sri/{batch_id}/calculate` and `GET /sri/{batch_id}` have no ownership check. `/sri/priority-queue` is accessible to any role (farmers/buyers) and leaks every farmer's ID and coordinates. Ignores `limit` query param; commits inside loop. | `backend/app/routers/sri.py` (L32–161) | **CONFIRMED** | Require batch ownership (farmer or admin) for calculate and get. Restrict priority queue to `STATIC_OPERATOR`, `VAN_OPERATOR`, `ADMIN` (403 for others). Filter queue so operators only receive batches relevant to their active assets (active bid, active booking, or eligible crop/radius). Support `limit` param. Batch DB commits. |
| **D** | **Maps Route Permissions & Range Validation:** `/maps/route` lacks coordinate range checks (`-90..90`, `-180..180`) and batch ownership checks. Missing backend forward geocoding endpoint. | `backend/app/routers/maps.py` (L14–50) | **CONFIRMED** | Add coordinate validation constraints (`Query(..., ge=..., le=...)`), verify batch ownership if `batch_id` is supplied, and provide backend forward search proxy with 1 req/s throttling. |
| **E** | **Frontend Direct Nominatim Fetch & Missing Throttling:** `frontend/js/maps.js` calls Nominatim directly from browser with custom User-Agent that browsers strip. Backend `reverse_geocode` has no rate limiter (1 req/s policy) and no memory/DB cache. | `frontend/js/maps.js` (L276, L326), `maps_service.py` (L180–195) | **CONFIRMED** | Route address search and reverse geocode through backend proxy with 1 req/sec rate limiting and in-memory TTL caching. |
| **F** | **In-Memory Daily Call Counter & Non-Optimal Destination Capping:** `_daily_routing_calls` is an in-memory dict that resets on reload. `destinations[:MAX_ROUTE_CALLS_PER_REQUEST]` takes arbitrary first items instead of nearest by straight-line distance. | `backend/app/services/maps_service.py` (L12, L172) | **CONFIRMED** | Sort candidate destinations by Haversine distance before slicing to `MAX_ROUTE_CALLS_PER_REQUEST`. |
| **G** | **Config JWT Secret Default:** Default JWT secret in `config.py` allows fallback if `.env` is omitted. | `backend/app/core/config.py` (L26) | **CONFIRMED** | Enforce validation requiring custom `JWT_SECRET` in production (`APP_ENV=production`). |
| **H** | **Hardcoded URLs in Frontend Config:** `API_BASE_URL` and `NOMINATIM_REVERSE_URL` hardcoded. | `frontend/js/config.js` (L10–20) | **CONFIRMED** | Use dynamic origin resolution `window.location.origin` where applicable. |
| **I** | **Documentation Discrepancies:** README mentions `MAX_ROUTE_CALLS_PER_DAY=1000` while `.env` default was 200. Stray empty `coldbridge.db` at root. | `README.md`, `backend/.env`, root folder | **CONFIRMED** | Align configuration values, delete empty root `coldbridge.db`. |
| **J** | **Localization Partial Coverage:** Only `farmer.html` contains `data-i18n` attributes. | `frontend/` HTML pages | **CONFIRMED** | Expand localization keys across other user views. |

---

## 4. Next Steps
With Phase C0 audit completed and recorded, proceed to **Phase C1** (Fixing Allocation Bug, Matching Ownership, and Bid Transparency), followed by **Phase C2** (SRI Authorization and Priority Queue Privacy).
