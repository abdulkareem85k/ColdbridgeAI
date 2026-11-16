/**
 * ColdBridge AI - Frontend Runtime Configuration Override Example
 *
 * Copy this file to `config.local.js` in the same directory (`frontend/js/config.local.js`)
 * to override default settings for deployed or customized environments without build tools.
 */
export const CONFIG_OVERRIDES = {
    // Override backend API endpoint (default: http://127.0.0.1:8000/api/v1)
    API_BASE_URL: "http://127.0.0.1:8000/api/v1",

    // Optional custom tile server or attribution:
    // OSM_TILE_URL: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    // OSM_ATTRIBUTION: '&copy; OpenStreetMap contributors'
};
