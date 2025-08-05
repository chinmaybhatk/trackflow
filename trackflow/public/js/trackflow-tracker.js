// TrackFlow Tracking Script
// This script can be embedded on external websites to track events

(function() {
    'use strict';

    // Configuration
    const TRACKFLOW_ENDPOINT = window.TRACKFLOW_ENDPOINT || '/api/method/trackflow.api.track_event';
    const TRACKFLOW_DOMAIN = window.TRACKFLOW_DOMAIN || window.location.origin;

    // TrackFlow Tracker Object
    const TrackFlowTracker = {
        // Initialize tracker
        init: function() {
            this.sessionId = this.getSessionId();
            this.visitorId = this.getVisitorId();
            this.pageLoadTime = Date.now();
            
            // Track page view on load
            this.trackPageView();
            
            // Set up event listeners
            this.setupEventListeners();
        },

        // Get or create session ID
        getSessionId: function() {
            let sessionId = sessionStorage.getItem('tf_session_id');
            if (!sessionId) {
                sessionId = this.generateId();
                sessionStorage.setItem('tf_session_id', sessionId);
            }
            return sessionId;
        },

        // Get or create visitor ID
        getVisitorId: function() {
            let visitorId = localStorage.getItem('tf_visitor_id');
            if (!visitorId) {
                visitorId = this.generateId();
                localStorage.setItem('tf_visitor_id', visitorId);
            }
            return visitorId;
        },

        // Generate unique ID
        generateId: function() {
            return 'tf_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        },

        // Get browser info
        getBrowserInfo: function() {
            const ua = navigator.userAgent;
            let browser = 'Unknown';
            
            if (ua.indexOf('Chrome') > -1) browser = 'Chrome';
            else if (ua.indexOf('Safari') > -1) browser = 'Safari';
            else if (ua.indexOf('Firefox') > -1) browser = 'Firefox';
            else if (ua.indexOf('MSIE') > -1 || ua.indexOf('Trident/') > -1) browser = 'IE';
            else if (ua.indexOf('Edge') > -1) browser = 'Edge';
            
            return {
                browser: browser,
                userAgent: ua,
                language: navigator.language || navigator.userLanguage,
                platform: navigator.platform,
                screenResolution: screen.width + 'x' + screen.height,
                viewport: window.innerWidth + 'x' + window.innerHeight,
                colorDepth: screen.colorDepth,
                timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
            };
        },

        // Get page info
        getPageInfo: function() {
            return {
                url: window.location.href,
                title: document.title,
                referrer: document.referrer,
                path: window.location.pathname,
                host: window.location.hostname,
                protocol: window.location.protocol,
                search: window.location.search,
                hash: window.location.hash
            };
        },

        // Track event
        track: function(eventType, eventData = {}) {
            const data = {
                event_type: eventType,
                event_data: eventData,
                session_id: this.sessionId,
                visitor_id: this.visitorId,
                timestamp: new Date().toISOString(),
                page_info: this.getPageInfo(),
                browser_info: this.getBrowserInfo(),
                time_on_page: Date.now() - this.pageLoadTime
            };

            // Send to server
            this.sendData(data);
        },

        // Send data to server
        sendData: function(data) {
            // Use sendBeacon if available for reliability
            if (navigator.sendBeacon) {
                const blob = new Blob([JSON.stringify(data)], { type: 'application/json' });
                navigator.sendBeacon(TRACKFLOW_ENDPOINT, blob);
            } else {
                // Fallback to fetch
                fetch(TRACKFLOW_ENDPOINT, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data),
                    keepalive: true
                }).catch(error => {
                    console.error('TrackFlow: Error sending data', error);
                });
            }
        },

        // Track page view
        trackPageView: function() {
            this.track('page_view', {
                source: this.getUTMParams()
            });
        },

        // Track click
        trackClick: function(element, additionalData = {}) {
            const data = {
                element_tag: element.tagName,
                element_id: element.id,
                element_class: element.className,
                element_text: element.textContent?.substring(0, 100),
                element_href: element.href,
                ...additionalData
            };
            
            this.track('click', data);
        },

        // Track form submission
        trackFormSubmit: function(form, additionalData = {}) {
            const data = {
                form_id: form.id,
                form_name: form.name,
                form_action: form.action,
                form_method: form.method,
                ...additionalData
            };
            
            this.track('form_submit', data);
        },

        // Track custom conversion
        trackConversion: function(conversionType, value = null, additionalData = {}) {
            const data = {
                conversion_type: conversionType,
                conversion_value: value,
                ...additionalData
            };
            
            this.track('conversion', data);
        },

        // Get UTM parameters
        getUTMParams: function() {
            const params = new URLSearchParams(window.location.search);
            const utmParams = {};
            
            ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content'].forEach(param => {
                if (params.has(param)) {
                    utmParams[param] = params.get(param);
                }
            });
            
            return utmParams;
        },

        // Set up event listeners
        setupEventListeners: function() {
            // Track clicks on tracked elements
            document.addEventListener('click', (e) => {
                const target = e.target.closest('[data-tf-track]');
                if (target) {
                    const trackData = target.dataset.tfTrack;
                    try {
                        const data = JSON.parse(trackData);
                        this.trackClick(target, data);
                    } catch (error) {
                        this.trackClick(target);
                    }
                }
            });

            // Track form submissions
            document.addEventListener('submit', (e) => {
                const form = e.target;
                if (form.dataset.tfTrackSubmit !== undefined) {
                    this.trackFormSubmit(form);
                }
            });

            // Track page unload
            window.addEventListener('beforeunload', () => {
                this.track('page_unload', {
                    time_on_page: Date.now() - this.pageLoadTime
                });
            });

            // Track scroll depth
            let maxScrollDepth = 0;
            let scrollTimeout;
            
            window.addEventListener('scroll', () => {
                clearTimeout(scrollTimeout);
                
                scrollTimeout = setTimeout(() => {
                    const scrollPercent = Math.round(
                        (window.scrollY + window.innerHeight) / document.documentElement.scrollHeight * 100
                    );
                    
                    if (scrollPercent > maxScrollDepth) {
                        maxScrollDepth = scrollPercent;
                        
                        // Track milestone scroll depths
                        if ([25, 50, 75, 90, 100].includes(maxScrollDepth)) {
                            this.track('scroll_depth', {
                                depth: maxScrollDepth
                            });
                        }
                    }
                }, 100);
            });
        }
    };

    // Auto-initialize if not explicitly disabled
    if (window.TRACKFLOW_AUTO_INIT !== false) {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => TrackFlowTracker.init());
        } else {
            TrackFlowTracker.init();
        }
    }

    // Expose to global scope
    window.TrackFlowTracker = TrackFlowTracker;

})();
