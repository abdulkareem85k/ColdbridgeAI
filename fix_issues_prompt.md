# Prompt: Fix the 6 Open Issues in ColdBridge AI

## Role
You are a senior full-stack engineer on **ColdBridge AI** (FastAPI + SQLAlchemy + Alembic backend, vanilla HTML/CSS/JS frontend). Fix the six issues below at the root cause. Make small, reviewable changes and prove each fix with a test or a browser check.

## Rules
- Vanilla HTML/CSS/ES modules only. No frameworks, no build step, no new runtime dependencies.
- Never weaken security: keep HttpOnly cookie auth, the `X-Requested-With` CSRF header, RBAC, and output escaping (`escapeHtml`).
- Do not change existing API behaviour except where stated.
- Keep the honesty labels (`DATA_SOURCE: SIMULATED`, "prototype") intact.
- Run the full test suite before and after. Report the counts.

## Issues and required fixes

### 1. Two tests fail in the full run
- **Root cause:** `tests/test_admin_simulation.py` creates a module-level `TestClient(app)` that uses the real dev database, bypassing the isolated test DB in `conftest.py`. It fails when `backend/coldbridge.db` is missing, and `/admin/reset-demo-data` can wipe real dev data.
- **Fix:** use the `client` and `db_session` fixtures, and seed with `seed_demo_data(db_session)` in a fixture. Remove the module-level client.
- **Done when:** the full suite passes with no `coldbridge.db` present.

### 2. Operator portals are not translated
- **Root cause:** `storage_operator.html` and `van_operator.html` have a language switcher but no `data-i18n` attributes.
- **Fix:** add `data-i18n` to navigation, headings, subtitles, buttons, form labels, options, modal titles and table headers (including those rendered inside JS templates). Add matching `en`, `hi`, `mr` keys to `frontend/js/i18n.js` (one key per line, so `tests/test_i18n_parity.py` can parse it).
- For text that mixes `<strong>`/`<code>`, add a `data-i18n-html` attribute (developer-authored strings only). Add a `MutationObserver` so content inserted later by `innerHTML` is translated.
- Reuse existing keys when the English text is identical.
- **Done when:** switching to Hindi or Marathi leaves no English in static UI text, and a test checks every `data-i18n` key exists in all three languages.

### 3. No audit log screen
- **Fix (backend):** add `GET /api/v1/admin/audit-logs` (ADMIN only) with `action` and `resource_type` filters, `limit` (1–200) and `offset`. Return `total`, `items` (parsed details, user email), and the available filter values. Never return secrets.
- **Fix (frontend):** create `frontend/admin.html` with three tabs: Overview (`/admin/stats`), Audit Log (filters, pagination, expandable details), Simulation (advance clock, reset demo data with confirm). Route `ADMIN` to it in `redirectByRole`.
- **Done when:** tests cover RBAC (403 for non-admin), filtering, pagination and validation (422), and the page works in a browser.

### 4. Tables overflow on phones
- **Fix:** every `<table>` must sit inside `.table-container` (`overflow-x: auto`). Let long tokens wrap (`overflow-wrap: anywhere`) and stack two-column form rows under 640px.
- **Done when:** at 390px width, `document.documentElement.scrollWidth - clientWidth === 0` on **every tab** of every portal.

### 5. README is out of date
- **Fix:** regenerate the directory tree from the real files, remove the `C:\Users\...` path (also in `docs/`), update the test count, document the admin portal and its demo account, and make the Localization and Offline notes accurate.
- **Done when:** every file in the README tree exists, and no personal path remains (`grep -rn "C:\\\\Users"`).

### 6. Leaflet loads from a CDN
- **Fix:** vendor Leaflet 1.9.4 (`leaflet.js`, `leaflet.css`, `images/`, license) into `frontend/vendor/leaflet/`. Point all pages and `js/maps.js` at it (use `new URL('../vendor/leaflet/...', import.meta.url)` inside the module).
- Be honest in docs: map **tiles** still need internet. Keep the Haversine/list fallback.
- **Done when:** no `unpkg.com` request is made, and a test guards against reintroducing it.

## Verification checklist
- [ ] `pytest` passes in full, from a clean checkout with no dev database.
- [ ] New tests: audit-log API, frontend quality (i18n keys, no CDN, tables wrapped, admin redirect).
- [ ] Browser check at 1280px and 390px for farmer, buyer, storage, van and admin pages: no console errors, no sideways page scroll.
- [ ] Hindi and Marathi screenshots of both operator pages.
- [ ] Admin login lands on `admin.html`; audit table filters and paginates.

## Output format
1. One short paragraph per issue: root cause, fix, evidence (test name or measurement).
2. List of changed and new files.
3. Final test result line.
4. Remaining limitations, stated honestly (for example: machine-written Hindi/Marathi needs native review).
