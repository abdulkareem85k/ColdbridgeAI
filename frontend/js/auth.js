import { apiRequest } from './api.js';

export async function login(email, password) {
    const user = await apiRequest('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password })
    });
    return user;
}

export async function register(payload) {
    const user = await apiRequest('/auth/register', {
        method: 'POST',
        body: JSON.stringify(payload)
    });
    return user;
}

export async function getMe() {
    try {
        const user = await apiRequest('/auth/me', { method: 'GET' });
        return user;
    } catch (err) {
        if (err.status === 401) {
            return null;
        }
        throw err;
    }
}

export async function logout() {
    try {
        await apiRequest('/auth/logout', { method: 'POST' });
    } catch (e) {
        console.warn('Logout request warning:', e);
    }
    window.location.href = 'index.html';
}

export function redirectByRole(user) {
    if (!user) {
        window.location.href = 'index.html';
        return;
    }
    switch (user.role) {
        case 'FARMER':
            window.location.href = 'farmer.html';
            break;
        case 'STATIC_OPERATOR':
        case 'VAN_OPERATOR':
            window.location.href = 'operator.html';
            break;
        case 'BUYER':
            window.location.href = 'buyer.html';
            break;
        case 'ADMIN':
            window.location.href = 'admin.html';
            break;
        default:
            window.location.href = 'farmer.html';
    }
}
