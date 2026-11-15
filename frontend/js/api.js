import { CONFIG } from './config.js';

/**
 * Shared API fetch wrapper for ColdBridge AI.
 *
 * SECURITY INVARIANTS:
 * 1. ALWAYS uses `credentials: 'include'` so HttpOnly cookies are automatically sent.
 * 2. ALWAYS includes `X-Requested-With: XMLHttpRequest` for backend CSRF verification.
 * 3. NEVER reads, stores, or manually attaches JWT tokens.
 */
export async function apiRequest(endpoint, options = {}) {
    const url = endpoint.startsWith('http') ? endpoint : `${CONFIG.API_BASE_URL}${endpoint}`;
    
    const headers = {
        'Accept': 'application/json',
        'X-Requested-With': 'XMLHttpRequest', // CSRF protection header
        ...(options.headers || {})
    };

    if (options.body && !(options.body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
    }

    const config = {
        ...options,
        headers,
        credentials: 'include' // Required for HttpOnly cookie session
    };

    try {
        const response = await fetch(url, config);
        
        let data = null;
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            data = await response.json();
        }

        if (!response.ok) {
            const errorMessage = (data && (data.detail || data.message)) 
                ? (typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail))
                : `HTTP Error ${response.status}: ${response.statusText}`;
            
            const error = new Error(errorMessage);
            error.status = response.status;
            error.data = data;
            throw error;
        }

        return data;
    } catch (err) {
        console.error(`[API Error] ${options.method || 'GET'} ${endpoint}:`, err.message);
        throw err;
    }
}
