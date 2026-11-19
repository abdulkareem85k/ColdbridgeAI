/**
 * ColdBridge AI - Product Website Interaction Logic
 * Decentralized Pay-Per-Use Cold Chain Logistics
 */

import { getMe, logout, redirectByRole } from './auth.js';

document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize navigation, automated hero video, and visual reveals
    setupNavbar();
    setupAutomatedHeroVideo();
    setupScrollReveals();

    // 2. Check auth state asynchronously in background without blocking UI
    setupAuthButtons().catch(() => {});
});

// =========================================================================
// 1. AUTHENTICATION BUTTONS
// =========================================================================
async function setupAuthButtons() {
    const navActions = document.getElementById('navAuthActions');
    if (!navActions) return;

    try {
        const user = await getMe();
        if (user && user.role) {
            const roleLabel = user.role.replace('_', ' ').toLowerCase();
            navActions.innerHTML = `
                <button type="button" class="btn-nav-outline" id="btnGoDashboard">
                    Dashboard (${roleLabel})
                </button>
                <button type="button" class="btn-nav-ghost" id="btnLogoutNav">
                    Logout
                </button>
            `;
            const btnDash = document.getElementById('btnGoDashboard');
            const btnOut = document.getElementById('btnLogoutNav');
            if (btnDash) btnDash.addEventListener('click', () => redirectByRole(user));
            if (btnOut) btnOut.addEventListener('click', logout);
            return;
        }
    } catch (_) {
        // Visitor is not logged in; show default actions
    }

    navActions.innerHTML = `
        <a href="login.html#login" class="btn-nav-outline" id="navBtnLogin">Login</a>
        <a href="login.html#register" class="btn-nav-fill" id="navBtnSignup">Sign Up</a>
    `;
}

// =========================================================================
// 2. NAVBAR SCROLL & MOBILE DRAWER
// =========================================================================
function setupNavbar() {
    const nav = document.querySelector('.site-nav');
    const hamburger = document.getElementById('navHamburger');
    const navLinks = document.getElementById('navLinks');

    if (nav) {
        const onScroll = () => {
            if (window.scrollY > 30) {
                nav.classList.add('scrolled');
            } else {
                nav.classList.remove('scrolled');
            }
        };
        window.addEventListener('scroll', onScroll, { passive: true });
        onScroll();
    }

    if (hamburger && navLinks) {
        hamburger.addEventListener('click', () => {
            const isOpen = navLinks.classList.toggle('mobile-open');
            hamburger.setAttribute('aria-expanded', String(isOpen));
        });

        navLinks.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                navLinks.classList.remove('mobile-open');
                hamburger.setAttribute('aria-expanded', 'false');
            });
        });
    }
}

// =========================================================================
// 3. AUTOMATED HERO DEMO VIDEO (Autoplay & Continuous Loop)
// =========================================================================
function setupAutomatedHeroVideo() {
    const heroVideo = document.getElementById('heroVideoPlayer');
    if (!heroVideo) return;

    // Strict browser autoplay policy requires muted and playsInline
    heroVideo.muted = true;
    heroVideo.playsInline = true;
    heroVideo.loop = true;
    heroVideo.autoplay = true;

    const attemptPlay = () => {
        const promise = heroVideo.play();
        if (promise !== undefined) {
            promise.catch(() => {
                // If strict browser policy blocked unprompted autoplay, start on first interaction
                const onUserGesture = () => {
                    heroVideo.play().catch(() => {});
                    window.removeEventListener('click', onUserGesture);
                    window.removeEventListener('scroll', onUserGesture);
                    window.removeEventListener('touchstart', onUserGesture);
                    window.removeEventListener('keydown', onUserGesture);
                };
                window.addEventListener('click', onUserGesture, { once: true, passive: true });
                window.addEventListener('scroll', onUserGesture, { once: true, passive: true });
                window.addEventListener('touchstart', onUserGesture, { once: true, passive: true });
                window.addEventListener('keydown', onUserGesture, { once: true, passive: true });
            });
        }
    };

    attemptPlay();

    // Ensure continuous auto-looping without pausing
    heroVideo.addEventListener('ended', () => {
        heroVideo.currentTime = 0;
        heroVideo.play().catch(() => {});
    });
}

// =========================================================================
// 4. SCROLL REVEAL ANIMATIONS (Respects prefers-reduced-motion)
// =========================================================================
function setupScrollReveals() {
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) return;

    const revealElements = document.querySelectorAll('.fade-up');
    if (!revealElements.length) return;

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.12 });

    revealElements.forEach(el => observer.observe(el));
}
