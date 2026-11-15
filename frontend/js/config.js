/**
 * ColdBridge AI - Frontend Configuration
 *
 * GOOGLE MAPS PLATFORM RULES:
 * - The browser key below must be restricted in the Google Cloud Console by:
 *   1. HTTP Referrer (e.g. http://127.0.0.1:5500/*, http://localhost:5500/*)
 *   2. API Restrictions (Maps JavaScript API and Places API (New) only)
 * - The backend server key is kept strictly in backend/.env and never exposed here.
 */
export const CONFIG = {
    API_BASE_URL: "http://127.0.0.1:8000/api/v1",
    GOOGLE_MAPS_BROWSER_KEY: "REPLACE_WITH_BROWSER_KEY_HTTP_REFERRER_RESTRICTED",
    GOOGLE_MAP_ID: "DEMO_MAP_ID",
    DEFAULT_CENTER: { lat: 19.9975, lng: 73.7898 }, // Nashik, Maharashtra
    DEFAULT_ZOOM: 11
};
