/**
 * ColdBridge AI - Frontend Configuration
 *
 * MAP PLATFORM: OPENSTREETMAP + LEAFLET.JS
 * - Uses OpenStreetMap standard raster tiles with Leaflet.js
 * - Reverse geocoding via OpenStreetMap Nominatim
 * - Road routing via OSRM (Open Source Routing Machine) or straight-line estimation
 * - 100% Free & Open-Source: No Google Cloud keys or proprietary billing accounts needed.
 */

// Default configuration settings
const DEFAULT_CONFIG = {
    API_BASE_URL: "http://127.0.0.1:8000/api/v1",
    
    // OpenStreetMap & Leaflet Settings
    OSM_TILE_URL: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    OSM_ATTRIBUTION: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    
    // Geographic defaults: Nashik, Maharashtra, India
    DEFAULT_CENTER: { lat: 19.9975, lng: 73.7898 },
    DEFAULT_ZOOM: 11
};

// Check for runtime window overrides if injected (e.g. window.COLDBRIDGE_CONFIG)
const windowOverrides = (typeof window !== 'undefined' && window.COLDBRIDGE_CONFIG) ? window.COLDBRIDGE_CONFIG : {};

// Optional runtime override via config.local.js (not required to exist; see config.example.js)
let localOverrides = {};
try {
    const localModule = await import('./config.local.js');
    if (localModule && localModule.CONFIG_OVERRIDES) {
        localOverrides = localModule.CONFIG_OVERRIDES;
    }
} catch (e) {
    // config.local.js is optional; defaults are safely preserved
}

export const CONFIG = {
    ...DEFAULT_CONFIG,
    ...windowOverrides,
    ...localOverrides
};
