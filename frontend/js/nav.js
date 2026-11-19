/**
 * ColdBridge AI - Enhanced Portal Navigation Bar (nav-v2)
 *
 * Progressive enhancement for portal pages (farmer.html, buyer.html, storage_operator.html, van_operator.html).
 * Implements a responsive 2-row layout, deep hash linking with retry, edge fade masks,
 * and full accessibility support (ARIA current, focus rings, roving arrow keys, prefers-reduced-motion).
 */

(function () {
    'use strict';

    let activeRetryTimer = null;

    function getScrollBehavior() {
        return window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth';
    }

    function injectNavStyles() {
        if (typeof document === 'undefined' || !document.head || document.getElementById('cb-nav-v2-styles')) return;
        const style = document.createElement('style');
        style.id = 'cb-nav-v2-styles';
        style.textContent = `
header.nav-v2 {
    display: flex !important;
    flex-direction: column !important;
    padding: 0 !important;
    gap: 0 !important;
    background: #ffffff !important;
    border-bottom: 1px solid #e2e8f0 !important;
    position: sticky !important;
    top: 0 !important;
    z-index: 1000 !important;
    width: 100% !important;
    box-sizing: border-box !important;
}
.nav-v2-top {
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    padding: 0.6rem 1.25rem !important;
    border-bottom: 1px solid #e2e8f0 !important;
    width: 100% !important;
    box-sizing: border-box !important;
}
.nav-v2-actions {
    display: flex !important;
    align-items: center !important;
    gap: 0.5rem !important;
    margin-left: auto !important;
}
.nav-v2-tabs-wrapper {
    position: relative !important;
    width: 100% !important;
    background: #ffffff !important;
    display: flex !important;
    align-items: center !important;
    padding: 0 !important;
    margin: 0 !important;
    box-sizing: border-box !important;
    overflow: hidden !important;
}
.nav-v2-tabs-strip {
    display: flex !important;
    align-items: center !important;
    gap: 0.35rem !important;
    padding: 0 1rem !important;
    width: 100% !important;
    overflow-x: auto !important;
    white-space: nowrap !important;
    flex-wrap: nowrap !important;
    scrollbar-width: none !important;
    -ms-overflow-style: none !important;
    scroll-behavior: smooth !important;
    -webkit-overflow-scrolling: touch !important;
    box-sizing: border-box !important;
}
.nav-v2-tabs-strip::-webkit-scrollbar {
    display: none !important;
}
header.nav-v2 .nav-link {
    display: inline-flex !important;
    align-items: center !important;
    padding: 0.65rem 0.85rem !important;
    color: #64748b !important;
    font-size: 0.9rem !important;
    font-weight: 500 !important;
    text-decoration: none !important;
    border-radius: 0 !important;
    border-bottom: 2px solid transparent !important;
    flex-shrink: 0 !important;
    white-space: nowrap !important;
    background: transparent !important;
    outline: none !important;
}
header.nav-v2 .nav-link:hover {
    color: #1b5e20 !important;
    background: transparent !important;
}
header.nav-v2 .nav-link.active,
header.nav-v2 .nav-link[aria-current="page"] {
    color: #1b5e20 !important;
    font-weight: 700 !important;
    border-bottom: 2px solid #1b5e20 !important;
    background: transparent !important;
}
header.nav-v2 .nav-link:focus-visible {
    outline: 2px solid #1b5e20 !important;
    outline-offset: -2px !important;
}
.nav-v2-tabs-strip.mask-right {
    -webkit-mask-image: linear-gradient(to right, #000 0%, #000 calc(100% - 2.5rem), transparent 100%) !important;
    mask-image: linear-gradient(to right, #000 0%, #000 calc(100% - 2.5rem), transparent 100%) !important;
}
.nav-v2-tabs-strip.mask-left {
    -webkit-mask-image: linear-gradient(to right, transparent 0%, #000 2.5rem, #000 100%) !important;
    mask-image: linear-gradient(to right, transparent 0%, #000 2.5rem, #000 100%) !important;
}
.nav-v2-tabs-strip.mask-both {
    -webkit-mask-image: linear-gradient(to right, transparent 0%, #000 2.5rem, #000 calc(100% - 2.5rem), transparent 100%) !important;
    mask-image: linear-gradient(to right, transparent 0%, #000 2.5rem, #000 calc(100% - 2.5rem), transparent 100%) !important;
}
@media (max-width: 640px) {
    .nav-v2-top {
        padding: 0.45rem 0.65rem !important;
    }
    .brand-badge {
        display: none !important;
    }
    .user-pill {
        padding: 0.15rem 0.35rem !important;
        background: transparent !important;
        gap: 0.25rem !important;
    }
    .user-pill span,
    #userName,
    #buyerName,
    #operatorName {
        display: none !important;
    }
    #btnLogout {
        display: inline-flex !important;
        padding: 0.25rem 0.55rem !important;
        font-size: 0.78rem !important;
    }
    #langSwitcher {
        font-size: 0.78rem !important;
        padding: 0.2rem 0.35rem !important;
    }
    .nav-v2-tabs-strip {
        padding: 0 0.5rem !important;
        gap: 0.2rem !important;
    }
    header.nav-v2 .nav-link {
        padding: 0.55rem 0.65rem !important;
        font-size: 0.85rem !important;
    }
}
`;
        document.head.appendChild(style);
    }

    function initNav() {
        const header = document.querySelector('header');
        if (!header) return;

        // Prevent double initialization
        if (header.classList.contains('nav-v2')) return;

        // Inject essential responsive V2 navigation styles to guarantee layout even with cached CSS
        injectNavStyles();

        const brand = header.querySelector('.brand');
        const nav = header.querySelector('nav');
        if (!brand || !nav) return;

        const links = Array.from(nav.querySelectorAll('a.nav-link'));
        const langSwitcher = document.getElementById('langSwitcher');
        const userPill = nav.querySelector('.user-pill');

        // 1. Build Row 1: Top bar (Brand on left, utilities on right)
        const rowTop = document.createElement('div');
        rowTop.className = 'nav-v2-top';

        // Move brand into Row 1
        rowTop.appendChild(brand);

        // Actions container for Row 1
        const rowActions = document.createElement('div');
        rowActions.className = 'nav-v2-actions';
        if (langSwitcher) {
            rowActions.appendChild(langSwitcher);
        }
        if (userPill) {
            rowActions.appendChild(userPill);
        }
        rowTop.appendChild(rowActions);

        // 2. Build Row 2: Horizontal scrollable tab strip
        const strip = document.createElement('div');
        strip.className = 'nav-v2-tabs-strip';
        strip.setAttribute('role', 'tablist');
        strip.setAttribute('aria-label', 'Portal Tabs');

        // Move tabs into strip
        links.forEach(link => {
            link.setAttribute('role', 'tab');
            strip.appendChild(link);
        });

        // Configure nav as tabs wrapper
        nav.className = 'nav-v2-tabs-wrapper';
        nav.setAttribute('aria-label', 'Portal Navigation');
        nav.innerHTML = '';
        nav.appendChild(strip);

        // Insert Row 1 before Row 2 nav
        header.classList.add('nav-v2');
        header.insertBefore(rowTop, nav);

        // 3. Edge fades / scroll mask logic
        function updateScrollMask() {
            const scrollLeft = Math.ceil(strip.scrollLeft);
            const scrollWidth = strip.scrollWidth;
            const clientWidth = strip.clientWidth;
            const maxScroll = scrollWidth - clientWidth;

            if (maxScroll <= 2) {
                strip.classList.remove('mask-left', 'mask-right', 'mask-both');
                return;
            }

            const canScrollLeft = scrollLeft > 2;
            const canScrollRight = scrollLeft < maxScroll - 2;

            if (canScrollLeft && canScrollRight) {
                strip.classList.add('mask-both');
                strip.classList.remove('mask-left', 'mask-right');
            } else if (canScrollLeft) {
                strip.classList.add('mask-left');
                strip.classList.remove('mask-right', 'mask-both');
            } else if (canScrollRight) {
                strip.classList.add('mask-right');
                strip.classList.remove('mask-left', 'mask-both');
            } else {
                strip.classList.remove('mask-left', 'mask-right', 'mask-both');
            }
        }

        strip.addEventListener('scroll', updateScrollMask, { passive: true });
        window.addEventListener('resize', updateScrollMask, { passive: true });

        // 4. Tab activation & aria-current handling
        function setActiveTab(activeLink, shouldScroll = true) {
            if (!activeLink) return;

            links.forEach(l => {
                if (l === activeLink) {
                    l.setAttribute('aria-current', 'page');
                    l.setAttribute('aria-selected', 'true');
                } else {
                    l.removeAttribute('aria-current');
                    l.setAttribute('aria-selected', 'false');
                }
            });

            if (shouldScroll) {
                activeLink.scrollIntoView({
                    behavior: getScrollBehavior(),
                    block: 'nearest',
                    inline: 'center'
                });
            }

            setTimeout(updateScrollMask, 50);
            setTimeout(updateScrollMask, 250);
        }

        // 5. Tab click listeners: update history hash & active indicator
        links.forEach(link => {
            link.addEventListener('click', () => {
                const href = link.getAttribute('href');
                if (href && href.startsWith('#')) {
                    if (window.history && window.history.replaceState) {
                        window.history.replaceState(null, '', href);
                    }
                }
                setActiveTab(link, true);
            });
        });

        // 6. Keyboard navigation: Arrow Left/Right/Up/Down, Home, End
        strip.addEventListener('keydown', (e) => {
            const activeEl = document.activeElement;
            const currentIndex = links.indexOf(activeEl);
            if (currentIndex === -1) return;

            let targetIndex = -1;

            switch (e.key) {
                case 'ArrowRight':
                case 'ArrowDown':
                    e.preventDefault();
                    targetIndex = (currentIndex + 1) % links.length;
                    break;
                case 'ArrowLeft':
                case 'ArrowUp':
                    e.preventDefault();
                    targetIndex = (currentIndex - 1 + links.length) % links.length;
                    break;
                case 'Home':
                    e.preventDefault();
                    targetIndex = 0;
                    break;
                case 'End':
                    e.preventDefault();
                    targetIndex = links.length - 1;
                    break;
                case ' ':
                    e.preventDefault();
                    activeEl.click();
                    return;
                default:
                    return;
            }

            if (targetIndex >= 0 && targetIndex < links.length) {
                const targetLink = links[targetIndex];
                targetLink.focus();
                targetLink.scrollIntoView({
                    behavior: getScrollBehavior(),
                    block: 'nearest',
                    inline: 'center'
                });
            }
        });

        // 7. Deep linking with retries (up to 30 x 150ms = 4.5s)
        function activateTabFromHash() {
            const hash = window.location.hash;
            if (!hash) {
                // If no hash in URL, mark currently active link
                const currentActive = links.find(l => l.classList.contains('active')) || links[0];
                if (currentActive) {
                    setActiveTab(currentActive, false);
                }
                updateScrollMask();
                return;
            }

            if (activeRetryTimer) {
                clearInterval(activeRetryTimer);
                activeRetryTimer = null;
            }

            let retries = 30;

            function attemptClick() {
                const currentHash = window.location.hash;
                if (!currentHash) {
                    clearInterval(activeRetryTimer);
                    activeRetryTimer = null;
                    return;
                }

                const targetLink = links.find(l => l.getAttribute('href') === currentHash);
                if (!targetLink) {
                    retries--;
                    if (retries <= 0) {
                        clearInterval(activeRetryTimer);
                        activeRetryTimer = null;
                    }
                    return;
                }

                const targetTabId = targetLink.getAttribute('data-tab');
                const targetContent = targetTabId ? document.getElementById(targetTabId) : null;

                // Trigger link click so page-level handlers switch tabs
                targetLink.click();

                // Check if page handler has activated the tab
                const isContentActive = targetContent ? targetContent.classList.contains('active') : true;
                const isLinkActive = targetLink.classList.contains('active');

                if (isContentActive && isLinkActive) {
                    clearInterval(activeRetryTimer);
                    activeRetryTimer = null;
                    setActiveTab(targetLink, true);
                    return;
                }

                retries--;
                if (retries <= 0) {
                    clearInterval(activeRetryTimer);
                    activeRetryTimer = null;
                    setActiveTab(targetLink, true);
                }
            }

            attemptClick();
            if (retries > 0) {
                activeRetryTimer = setInterval(attemptClick, 150);
            }
        }

        // Listen for hashchange and popstate events (e.g. browser back/forward)
        window.addEventListener('hashchange', activateTabFromHash);
        window.addEventListener('popstate', activateTabFromHash);

        // Run deep link check on initialization
        activateTabFromHash();

        // Initial scroll mask calculation
        setTimeout(updateScrollMask, 50);
        setTimeout(updateScrollMask, 300);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initNav);
    } else {
        initNav();
    }
})();
