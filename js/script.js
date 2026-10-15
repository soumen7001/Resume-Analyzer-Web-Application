/**
 * Resume Analyzer — Shared Utilities
 * Navbar, notifications, health check — used on all pages.
 */

(function () {
    'use strict';

    const API_BASE_URL = 'http://localhost:5000';
    window.RESUME_ANALYZER = window.RESUME_ANALYZER || {};
    window.RESUME_ANALYZER.API_BASE_URL = API_BASE_URL;

    // ==========================================
    // Notification System
    // ==========================================
    window.RESUME_ANALYZER.showNotification = function (message, type = 'info') {
        const notification = document.getElementById('notification');
        if (!notification) return;
        notification.textContent = message;
        notification.className = `notification ${type} active`;
        clearTimeout(notification._timeout);
        notification._timeout = setTimeout(() => {
            notification.classList.remove('active');
        }, 4500);
    };

    // ==========================================
    // Loading Overlay
    // ==========================================
    window.RESUME_ANALYZER.showLoading = function (text = 'Analyzing your resume...') {
        const overlay = document.getElementById('loadingOverlay');
        const loadingText = document.getElementById('loadingText');
        if (loadingText) loadingText.textContent = text;
        if (overlay) overlay.classList.add('active');
    };

    window.RESUME_ANALYZER.hideLoading = function () {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) overlay.classList.remove('active');
    };

    // ==========================================
    // Score Utilities
    // ==========================================
    window.RESUME_ANALYZER.getScoreStatus = function (score) {
        if (score >= 80) return { label: 'Excellent', cls: 'status-excellent' };
        if (score >= 60) return { label: 'Good', cls: 'status-good' };
        if (score >= 40) return { label: 'Fair', cls: 'status-fair' };
        return { label: 'Needs Work', cls: 'status-poor' };
    };

    window.RESUME_ANALYZER.getScoreColor = function (score) {
        if (score >= 80) return '#10b981';
        if (score >= 60) return '#3b82f6';
        if (score >= 40) return '#f59e0b';
        return '#ef4444';
    };

    /**
     * Sanitize a string to prevent XSS when inserting resume content into innerHTML.
     */
    window.RESUME_ANALYZER.sanitize = function (str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    };

    // ==========================================
    // Navbar: scroll shadow + mobile toggle
    // ==========================================
    function initNavbar() {
        const navbar = document.getElementById('navbar');
        const toggle = document.getElementById('navbarToggle');
        const nav = document.getElementById('navbarNav');

        if (navbar) {
            window.addEventListener('scroll', () => {
                navbar.classList.toggle('scrolled', window.scrollY > 20);
            });
        }

        if (toggle && nav) {
            toggle.addEventListener('click', () => {
                nav.classList.toggle('open');
                toggle.textContent = nav.classList.contains('open') ? '✕' : '☰';
            });

            // Close menu when a link is clicked
            nav.querySelectorAll('a').forEach(link => {
                link.addEventListener('click', () => {
                    nav.classList.remove('open');
                    toggle.textContent = '☰';
                });
            });
        }

        // Mark active link
        const path = window.location.pathname;
        const filename = path.split('/').pop() || 'index.html';
        document.querySelectorAll('.navbar-nav a').forEach(link => {
            const href = link.getAttribute('href') || '';
            if (href === filename || (filename === '' && href === 'index.html')) {
                link.classList.add('active');
            }
        });

        // Footer year
        const yearEl = document.getElementById('footerYear');
        if (yearEl) yearEl.textContent = new Date().getFullYear();
    }

    // ==========================================
    // Backend Health Check
    // ==========================================
    async function checkHealth() {
        const dot = document.getElementById('healthDot');
        const label = document.getElementById('healthLabel');
        try {
            const res = await fetch(`${API_BASE_URL}/health`, { signal: AbortSignal.timeout(4000) });
            const data = await res.json();
            if (data.status === 'healthy') {
                if (dot) { dot.classList.add('healthy'); dot.title = 'Backend online'; }
                if (label) label.textContent = 'API Online';
                return true;
            }
        } catch (_) {
            if (dot) { dot.classList.add('offline'); dot.title = 'Backend offline'; }
            if (label) { label.textContent = 'API Offline'; label.style.color = '#ef4444'; }
            // Only show warning on analyzer page to avoid nagging users on every page
            if (window.location.pathname.includes('analyzer')) {
                window.RESUME_ANALYZER.showNotification(
                    '⚠️ Backend server not detected. Run: cd backend && python app.py',
                    'error'
                );
            }
        }
        return false;
    }

    // ==========================================
    // Init
    // ==========================================
    function init() {
        initNavbar();
        checkHealth();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();