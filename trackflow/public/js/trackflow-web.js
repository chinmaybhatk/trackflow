// Copyright (c) 2024, Chinmay Bhat and contributors
// For license information, please see license.txt

// TrackFlow Web Tracking Enhancement
(function() {
    'use strict';
    
    // Wait for TrackFlow to be loaded
    function enhanceTracking() {
        if (!window.TrackFlow) {
            setTimeout(enhanceTracking, 100);
            return;
        }
        
        // Track all tracked links
        document.querySelectorAll('a[data-trackflow]').forEach(function(link) {
            link.addEventListener('click', function(e) {
                // Track click event
                window.TrackFlow.track('tracked_link_click', {
                    link_id: link.getAttribute('data-trackflow'),
                    campaign: link.getAttribute('data-trackflow-campaign'),
                    destination: link.href
                });
            });
        });
        
        // Track form interactions
        document.querySelectorAll('form[data-trackflow-form]').forEach(function(form) {
            // Track form views
            window.TrackFlow.track('form_view', {
                form_id: form.getAttribute('data-trackflow-form'),
                form_name: form.getAttribute('data-trackflow-name')
            });
            
            // Track form field interactions
            let interacted = false;
            form.addEventListener('focus', function(e) {
                if (!interacted && e.target.tagName === 'INPUT') {
                    interacted = true;
                    window.TrackFlow.track('form_interaction', {
                        form_id: form.getAttribute('data-trackflow-form'),
                        field: e.target.name
                    });
                }
            }, true);
            
            // Track form abandonment
            let formStarted = false;
            form.addEventListener('input', function() {
                formStarted = true;
            });
            
            window.addEventListener('beforeunload', function() {
                if (formStarted && !form.submitted) {
                    window.TrackFlow.track('form_abandoned', {
                        form_id: form.getAttribute('data-trackflow-form')
                    });
                }
            });
            
            // Track form submission
            form.addEventListener('submit', function() {
                form.submitted = true;
                window.TrackFlow.track('form_submitted', {
                    form_id: form.getAttribute('data-trackflow-form')
                });
            });
        });
        
        // Track scroll depth
        let maxScroll = 0;
        let ticking = false;
        
        function updateScrollProgress() {
            let scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
            let scrollProgress = Math.round((window.scrollY / scrollHeight) * 100);
            
            if (scrollProgress > maxScroll) {
                maxScroll = scrollProgress;
                
                // Track milestones
                if (maxScroll >= 25 && maxScroll < 50) {
                    window.TrackFlow.track('scroll_depth', { depth: 25 });
                } else if (maxScroll >= 50 && maxScroll < 75) {
                    window.TrackFlow.track('scroll_depth', { depth: 50 });
                } else if (maxScroll >= 75 && maxScroll < 90) {
                    window.TrackFlow.track('scroll_depth', { depth: 75 });
                } else if (maxScroll >= 90) {
                    window.TrackFlow.track('scroll_depth', { depth: 90 });
                }
            }
            
            ticking = false;
        }
        
        window.addEventListener('scroll', function() {
            if (!ticking) {
                window.requestAnimationFrame(updateScrollProgress);
                ticking = true;
            }
        });
        
        // Track time on page
        let startTime = Date.now();
        let timeTracked = false;
        
        function trackTimeOnPage() {
            if (!timeTracked) {
                let timeOnPage = Math.round((Date.now() - startTime) / 1000);
                
                if (timeOnPage >= 30) {
                    window.TrackFlow.track('time_on_page', {
                        seconds: timeOnPage,
                        milestone: '30s'
                    });
                    timeTracked = true;
                }
            }
        }
        
        // Check every 5 seconds
        setInterval(trackTimeOnPage, 5000);
        
        // Track when user leaves
        window.addEventListener('beforeunload', function() {
            let timeOnPage = Math.round((Date.now() - startTime) / 1000);
            window.TrackFlow.track('page_exit', {
                time_on_page: timeOnPage,
                max_scroll_depth: maxScroll
            });
        });
    }
    
    // Start enhancement
    if (document.readyState === 'complete') {
        enhanceTracking();
    } else {
        window.addEventListener('load', enhanceTracking);
    }
})();
