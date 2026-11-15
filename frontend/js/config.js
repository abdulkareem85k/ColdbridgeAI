/**
 * ColdBridge AI - Frontend Configuration
 *
 * MAP PLATFORM: OPENSTREETMAP + LEAFLET.JS
 * - Uses OpenStreetMap standard raster tiles with Leaflet.js
 * - Reverse geocoding via OpenStreetMap Nominatim
 * - Road routing via OSRM (Open Source Routing Machine) or straight-line estimation
 * - 100% Free & Open-Source: No Google Cloud keys or proprietary billing accounts needed.
 */
export const CONFIG = {
    API_BASE_URL: "http://127.0.0.1:8000/api/v1",
    
    // OpenStreetMap & Leaflet Settings
    OSM_TILE_URL: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    OSM_ATTRIBUTION: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    NOMINATIM_REVERSE_URL: "https://nominatim.openstreetmap.org/reverse",
    
    // Geographic defaults: Nashik, Maharashtra, India
    DEFAULT_CENTER: { lat: 19.9975, lng: 73.7898 },
    DEFAULT_ZOOM: 11
};
