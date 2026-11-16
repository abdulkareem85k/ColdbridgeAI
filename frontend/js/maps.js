import { CONFIG } from './config.js';
import { apiRequest } from './api.js';

let leafletLoadedPromise = null;

/**
 * Dynamically load Leaflet library and stylesheet if not already loaded.
 */
export function ensureLeafletLoaded() {
    if (window.L) {
        return Promise.resolve(window.L);
    }
    if (leafletLoadedPromise) {
        return leafletLoadedPromise;
    }

    leafletLoadedPromise = new Promise((resolve, reject) => {
        // Load CSS
        if (!document.querySelector('link[data-leaflet-css]')) {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
            link.setAttribute('data-leaflet-css', 'true');
            document.head.appendChild(link);
        }

        // Load JS
        const script = document.createElement('script');
        script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
        script.crossOrigin = '';
        script.onload = () => resolve(window.L);
        script.onerror = (err) => reject(new Error('Failed to load Leaflet.js library'));
        document.head.appendChild(script);
    });

    return leafletLoadedPromise;
}

/**
 * Escape HTML to prevent XSS vulnerabilities in map popups.
 */
export function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

/**
 * Initialize a Leaflet map attached to elementId.
 */
export async function initMap(elementId, options = {}) {
    const L = await ensureLeafletLoaded();
    const container = document.getElementById(elementId);
    if (!container) {
        throw new Error(`Map container #${elementId} not found`);
    }

    // Reset container if previously initialized
    if (container._leaflet_id) {
        container._leaflet_id = null;
        container.innerHTML = '';
    }

    const center = options.center || [CONFIG.DEFAULT_CENTER.lat, CONFIG.DEFAULT_CENTER.lng];
    const zoom = options.zoom || CONFIG.DEFAULT_ZOOM;

    const map = L.map(elementId, {
        zoomControl: true,
        scrollWheelZoom: true
    }).setView(center, zoom);

    // Add OpenStreetMap raster tile layer with attribution
    L.tileLayer(CONFIG.OSM_TILE_URL, {
        maxZoom: 19,
        attribution: CONFIG.OSM_ATTRIBUTION
    }).addTo(map);

    return map;
}

/**
 * Create custom SVG-styled Leaflet Marker for Static Rooms, Mobile Vans, and Farms.
 */
export async function createMarker(map, { lat, lng, type = 'STATIC', title = '', popupHtml = '', isDraggable = false, onDragEnd = null }) {
    const L = await ensureLeafletLoaded();

    let color = '#15803d'; // Green for Static Room
    let symbol = '🏭';
    let typeLabel = 'Room';

    if (type === 'MOBILE') {
        color = '#0284c7'; // Blue for Mobile Van
        symbol = '🚐';
        typeLabel = 'Van';
    } else if (type === 'FARM') {
        color = '#b45309'; // Amber for Farm / Harvest batch
        symbol = '🌾';
        typeLabel = 'Farm';
    }

    const iconHtml = `
        <div style="
            background-color: ${color};
            color: #fff;
            width: 32px;
            height: 32px;
            border-radius: 50% 50% 50% 0;
            transform: rotate(-45deg);
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 2px 5px rgba(0,0,0,0.3);
            border: 2px solid #ffffff;
            cursor: pointer;
        ">
            <span style="transform: rotate(45deg); font-size: 14px;">${symbol}</span>
        </div>
    `;

    const customIcon = L.divIcon({
        className: 'custom-map-pin',
        html: iconHtml,
        iconSize: [32, 32],
        iconAnchor: [16, 32],
        popupAnchor: [0, -32]
    });

    const marker = L.marker([lat, lng], {
        icon: customIcon,
        title: `${typeLabel}: ${title}`,
        draggable: isDraggable
    }).addTo(map);

    if (popupHtml) {
        marker.bindPopup(popupHtml);
    }

    if (isDraggable && onDragEnd) {
        marker.on('dragend', (e) => {
            const pos = e.target.getLatLng();
            onDragEnd(pos.lat, pos.lng);
        });
    }

    return marker;
}

/**
 * Fit map viewport to encompass all markers.
 */
export async function fitToMarkers(map, markers = []) {
    const L = await ensureLeafletLoaded();
    if (!markers || markers.length === 0) return;

    const group = L.featureGroup(markers);
    map.fitBounds(group.getBounds().pad(0.15));
}

/**
 * Draw road route line on Leaflet map.
 */
export async function drawRoute(map, coordinates = [], options = {}) {
    const L = await ensureLeafletLoaded();
    if (!coordinates || coordinates.length === 0) return null;

    // Convert GeoJSON [lon, lat] pairs to Leaflet [lat, lon] pairs if needed
    const latLngs = coordinates.map(c => {
        if (Array.isArray(c)) {
            return c[0] > 60 ? [c[1], c[0]] : [c[0], c[1]];
        }
        return [c.lat, c.lng];
    });

    const polyline = L.polyline(latLngs, {
        color: options.color || '#2563eb',
        weight: 5,
        opacity: 0.8,
        dashArray: options.isEstimated ? '6, 8' : null
    }).addTo(map);

    map.fitBounds(polyline.getBounds().pad(0.15));
    return polyline;
}

/**
 * Mount an interactive OpenStreetMap + Leaflet location picker.
 * Includes address search, map click, draggable marker, and GPS locate button.
 */
export async function mountLocationPicker(containerId, { initialLat = 19.9975, initialLng = 73.7898, onChange }) {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = `
        <div class="location-picker-widget" style="border: 1px solid var(--border); border-radius: var(--radius-md); overflow: hidden; background: #fff;">
            <div style="padding: 0.75rem; background: #f8fafc; border-bottom: 1px solid var(--border); display: flex; gap: 0.5rem; align-items: center;">
                <input type="text" id="pickerSearchInput" placeholder="🔍 Search address in Maharashtra (e.g. Nashik APMC, Pune)..." 
                       style="flex: 1; padding: 0.4rem 0.6rem; border: 1px solid var(--border); border-radius: var(--radius-sm); font-size: 0.85rem;">
                <button type="button" id="pickerBtnSearch" class="btn btn-secondary btn-sm" title="Search Address">
                    Search
                </button>
                <button type="button" id="pickerBtnLocate" class="btn btn-secondary btn-sm" title="Use My Current GPS Location">
                    📍 My Location
                </button>
            </div>
            <div id="pickerMapElement" style="height: 250px; width: 100%;"></div>
            <div style="padding: 0.5rem 0.75rem; background: #f8fafc; font-size: 0.8rem; color: var(--text-muted); display: flex; justify-content: space-between; align-items: center;">
                <span id="pickerAddressText">Selected: 19.9975, 73.7898 (Click map or drag pin)</span>
                <span class="badge badge-source-live">OpenStreetMap</span>
            </div>
        </div>
    `;

    let map = null;
    let marker = null;
    let currentLat = initialLat;
    let currentLng = initialLng;

    try {
        const L = await ensureLeafletLoaded();
        map = await initMap('pickerMapElement', {
            center: [initialLat, initialLng],
            zoom: 12
        });

        // Draggable Pin
        marker = await createMarker(map, {
            lat: currentLat,
            lng: currentLng,
            type: 'FARM',
            title: 'Selected Location',
            isDraggable: true,
            onDragEnd: async (lat, lng) => {
                currentLat = lat;
                currentLng = lng;
                await updateLocation(lat, lng);
            }
        });

        // Map Click Handler
        map.on('click', async (e) => {
            currentLat = e.latlng.lat;
            currentLng = e.latlng.lng;
            marker.setLatLng(e.latlng);
            await updateLocation(currentLat, currentLng);
        });
    } catch (err) {
        console.warn('Map initialization failed (offline mode):', err);
        const mapEl = document.getElementById('pickerMapElement');
        if (mapEl) {
            mapEl.innerHTML = `
                <div style="height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center; background: #f8fafc; padding: 1rem; text-align: center;">
                    <div style="font-weight: 600; color: var(--text-muted); margin-bottom: 0.5rem;">📡 Offline / Fallback Location Mode</div>
                    <div style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.75rem;">Interactive map tiles offline. Select default Maharashtra location:</div>
                    <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; justify-content: center;">
                        <button type="button" class="btn btn-secondary btn-sm preset-btn" data-lat="19.9975" data-lng="73.7898">Nashik (19.99, 73.78)</button>
                        <button type="button" class="btn btn-secondary btn-sm preset-btn" data-lat="18.5204" data-lng="73.8567">Pune (18.52, 73.85)</button>
                        <button type="button" class="btn btn-secondary btn-sm preset-btn" data-lat="16.9902" data-lng="73.3120">Ratnagiri (16.99, 73.31)</button>
                    </div>
                </div>
            `;
            mapEl.querySelectorAll('.preset-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    const lat = parseFloat(btn.dataset.lat);
                    const lng = parseFloat(btn.dataset.lng);
                    document.getElementById('pickerAddressText').textContent = `Selected: ${lat}, ${lng} (${btn.textContent.split(' ')[0]})`;
                    if (onChange) onChange({ lat, lng, address: btn.textContent });
                });
            });
        }
    }

    async function updateLocation(lat, lng, knownAddress = null) {
        let address = knownAddress;
        const addressEl = document.getElementById('pickerAddressText');
        if (addressEl) {
            addressEl.textContent = `Resolving address for ${lat.toFixed(4)}, ${lng.toFixed(4)}...`;
        }

        if (!address) {
            try {
                // Call backend reverse-geocoding proxy
                const data = await apiRequest(`/maps/reverse-geocode?lat=${lat}&lng=${lng}`);
                if (data && data.address) {
                    address = data.address;
                } else {
                    address = 'Address unavailable – coordinates saved';
                }
            } catch (e) {
                // Keep selected marker and coordinates, never throw or lose selection
                address = 'Address unavailable – coordinates saved';
            }
        }

        const displayText = address || `Coordinates: ${lat.toFixed(4)}, ${lng.toFixed(4)}`;
        if (addressEl) {
            addressEl.textContent = `Selected: ${displayText}`;
        }

        if (onChange) {
            onChange({ lat, lng, address: displayText });
        }
    }

    // Geolocation "Use My Location"
    document.getElementById('pickerBtnLocate').addEventListener('click', () => {
        if (!navigator.geolocation) {
            alert('Geolocation is not supported by your browser.');
            return;
        }
        navigator.geolocation.getCurrentPosition(
            async (pos) => {
                const lat = pos.coords.latitude;
                const lng = pos.coords.longitude;
                map.setView([lat, lng], 13);
                marker.setLatLng([lat, lng]);
                await updateLocation(lat, lng);
            },
            (err) => {
                alert('Could not obtain current location: ' + err.message);
            }
        );
    });

    // Explicit Address Search on submit (button click or Enter key)
    // NOTE: Debounced search-as-you-type is removed to respect Nominatim usage policy
    async function executeSearch() {
        const searchInput = document.getElementById('pickerSearchInput');
        if (!searchInput) return;
        const query = searchInput.value.trim();
        if (query.length < 3) return;

        const addressEl = document.getElementById('pickerAddressText');
        if (addressEl) {
            addressEl.textContent = `Searching for "${query}"...`;
        }

        try {
            const results = await apiRequest(`/maps/search?q=${encodeURIComponent(query)}&limit=1`);
            if (results && results.length > 0) {
                const first = results[0];
                const lat = parseFloat(first.lat != null ? first.lat : first.latitude);
                const lng = parseFloat(first.lon != null ? first.lon : first.longitude);
                if (map && marker) {
                    map.setView([lat, lng], 13);
                    marker.setLatLng([lat, lng]);
                }
                await updateLocation(lat, lng, first.display_name);
            } else {
                if (addressEl) {
                    addressEl.textContent = `Location not found for "${query}". Coordinates unchanged.`;
                }
            }
        } catch (err) {
            console.warn('Address search error:', err);
            if (addressEl) {
                addressEl.textContent = 'Address search service unavailable. Coordinates unchanged.';
            }
        }
    }

    const searchInput = document.getElementById('pickerSearchInput');
    const searchBtn = document.getElementById('pickerBtnSearch');
    if (searchBtn) {
        searchBtn.addEventListener('click', executeSearch);
    }
    if (searchInput) {
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                executeSearch();
            }
        });
    }

    // Trigger initial resolution
    setTimeout(() => {
        map.invalidateSize();
    }, 200);

    return { map, marker };
}
