/**
 * ColdBridge AI - Shared Operator Common Logic (Phase E1)
 * Shared utilities for storage_operator.html and van_operator.html.
 * Session management is strictly handled via HttpOnly cookies (Zero token handling in JS).
 */

import { getMe, logout, redirectByRole } from './auth.js';
import { apiRequest } from './api.js';
import { initI18n, setLanguage, getLanguage, t } from './i18n.js';

export async function initOperatorSession(expectedRole) {
    try {
        const user = await getMe();
        if (!user) {
            window.location.href = 'login.html';
            return null;
        }

        // Enforce role-specific panel boundaries (allowing STORAGE_OPERATOR as an alias for STATIC_OPERATOR)
        const isStorageMatch = (expectedRole === 'STATIC_OPERATOR' || expectedRole === 'STORAGE_OPERATOR') &&
            (user.role === 'STATIC_OPERATOR' || user.role === 'STORAGE_OPERATOR');

        if (user.role !== expectedRole && !isStorageMatch && user.role !== 'ADMIN') {
            redirectByRole(user);
            return null;
        }

        return user;
    } catch (err) {
        console.error('Session verification failed:', err);
        window.location.href = 'login.html';
        return null;
    }
}

export function setupLangSwitcher(selectId = 'langSwitcher') {
    initI18n();
    const switcher = document.getElementById(selectId);
    if (switcher) {
        switcher.value = getLanguage();
        switcher.addEventListener('change', (e) => {
            setLanguage(e.target.value);
        });
    }
}

export function setupTabs(navSelector = 'nav .nav-link', tabClass = '.tab-content', defaultTab = null) {
    const navLinks = document.querySelectorAll(navSelector);
    const tabs = document.querySelectorAll(tabClass);

    function switchTab(tabId) {
        tabs.forEach(t => t.classList.remove('active'));
        navLinks.forEach(l => l.classList.remove('active'));

        const targetTab = document.getElementById(tabId);
        if (targetTab) {
            targetTab.classList.add('active');
        }

        const activeLink = Array.from(navLinks).find(l => l.getAttribute('data-tab') === tabId);
        if (activeLink) {
            activeLink.classList.add('active');
        }
    }

    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const tabId = link.getAttribute('data-tab');
            if (tabId) {
                switchTab(tabId);
                const href = link.getAttribute('href');
                if (href && href.startsWith('#')) {
                    history.pushState(null, '', href);
                }
            }
        });
    });

    // Check initial hash
    if (window.location.hash) {
        const hash = window.location.hash;
        const matchingLink = Array.from(navLinks).find(l => l.getAttribute('href') === hash);
        if (matchingLink) {
            const tabId = matchingLink.getAttribute('data-tab');
            switchTab(tabId);
            return;
        }
    }

    if (defaultTab) {
        switchTab(defaultTab);
    }
}

export function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    const div = document.createElement('div');
    div.textContent = String(str);
    return div.innerHTML;
}

export function formatDate(isoStr) {
    if (!isoStr) return 'N/A';
    try {
        const d = new Date(isoStr);
        return d.toLocaleDateString('en-IN', {
            day: 'numeric',
            month: 'short',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch (_) {
        return isoStr;
    }
}

export function getStatusBadge(status) {
    const s = (status || '').toUpperCase();
    let bg = '#6b7280';
    let text = '#ffffff';

    if (s === 'RESERVED') { bg = '#fef3c7'; text = '#b45309'; }
    else if (s === 'CONFIRMED') { bg = '#dbeafe'; text = '#1d4ed8'; }
    else if (s === 'PICKUP_SCHEDULED') { bg = '#e0e7ff'; text = '#4338ca'; }
    else if (s === 'PRODUCE_RECEIVED') { bg = '#d1fae5'; text = '#065f46'; }
    else if (s === 'IN_STORAGE') { bg = '#ecfdf5'; text = '#047857'; }
    else if (s === 'COMPLETED') { bg = '#dcfce7'; text = '#15803d'; }
    else if (s === 'CANCELLED' || s === 'EXPIRED') { bg = '#fee2e2'; text = '#b91c1c'; }

    return `<span class="badge" style="background:${bg}; color:${text}; font-weight:700;">${escapeHtml(s)}</span>`;
}
