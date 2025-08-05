// TrackFlow Main JavaScript

// TrackFlow namespace
window.TrackFlow = window.TrackFlow || {};

(function(TrackFlow) {
    'use strict';

    // Configuration
    TrackFlow.config = {
        apiEndpoint: '/api/method/trackflow.api',
        refreshInterval: 30000, // 30 seconds
        chartColors: {
            primary: '#2490ef',
            secondary: '#5f6368',
            success: '#00c853',
            warning: '#ff9800',
            danger: '#f44336'
        }
    };

    // Utility functions
    TrackFlow.utils = {
        // Format numbers with commas
        formatNumber: function(num) {
            return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
        },

        // Format percentage
        formatPercent: function(num, decimals = 1) {
            return num.toFixed(decimals) + '%';
        },

        // Copy to clipboard
        copyToClipboard: function(text) {
            if (navigator.clipboard) {
                navigator.clipboard.writeText(text).then(function() {
                    frappe.show_alert({
                        message: __('Copied to clipboard'),
                        indicator: 'green'
                    });
                });
            } else {
                // Fallback for older browsers
                const textarea = document.createElement('textarea');
                textarea.value = text;
                textarea.style.position = 'fixed';
                textarea.style.opacity = '0';
                document.body.appendChild(textarea);
                textarea.select();
                document.execCommand('copy');
                document.body.removeChild(textarea);
                frappe.show_alert({
                    message: __('Copied to clipboard'),
                    indicator: 'green'
                });
            }
        },

        // Debounce function
        debounce: function(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },

        // Generate QR Code
        generateQRCode: function(text, container, size = 200) {
            if (typeof QRCode !== 'undefined') {
                new QRCode(container, {
                    text: text,
                    width: size,
                    height: size,
                    colorDark: '#000000',
                    colorLight: '#ffffff',
                    correctLevel: QRCode.CorrectLevel.H
                });
            } else {
                console.warn('QRCode library not loaded');
            }
        }
    };

    // API functions
    TrackFlow.api = {
        // Call TrackFlow API
        call: function(method, args = {}) {
            return frappe.call({
                method: `trackflow.api.${method}`,
                args: args
            });
        },

        // Get dashboard stats
        getDashboardStats: function(filters = {}) {
            return this.call('get_dashboard_stats', { filters });
        },

        // Get click analytics
        getClickAnalytics: function(link_id, filters = {}) {
            return this.call('get_click_analytics', { link_id, filters });
        },

        // Generate short link
        generateShortLink: function(data) {
            return this.call('generate_short_link', { data });
        },

        // Get campaign performance
        getCampaignPerformance: function(campaign_id, filters = {}) {
            return this.call('get_campaign_performance', { campaign_id, filters });
        }
    };

    // UI Components
    TrackFlow.ui = {
        // Show loading state
        showLoading: function(container) {
            $(container).html(`
                <div class="tf-loading">
                    <div class="spinner"></div>
                </div>
            `);
        },

        // Show empty state
        showEmptyState: function(container, options = {}) {
            const defaults = {
                icon: 'fa fa-inbox',
                title: 'No data found',
                description: 'There is no data to display at the moment.',
                buttonText: '',
                buttonAction: null
            };
            
            const config = Object.assign(defaults, options);
            
            let html = `
                <div class="tf-empty-state">
                    <div class="icon"><i class="${config.icon}"></i></div>
                    <div class="title">${config.title}</div>
                    <div class="description">${config.description}</div>
            `;
            
            if (config.buttonText && config.buttonAction) {
                html += `<button class="btn btn-primary" onclick="${config.buttonAction}">${config.buttonText}</button>`;
            }
            
            html += '</div>';
            
            $(container).html(html);
        },

        // Render stats card
        renderStatsCard: function(data) {
            const changeClass = data.change >= 0 ? 'positive' : 'negative';
            const changeIcon = data.change >= 0 ? 'fa-arrow-up' : 'fa-arrow-down';
            
            return `
                <div class="tf-stats-card">
                    <div class="title">${data.title}</div>
                    <div class="value">${TrackFlow.utils.formatNumber(data.value)}</div>
                    ${data.change !== undefined ? `
                        <div class="change ${changeClass}">
                            <i class="fa ${changeIcon}"></i>
                            <span>${Math.abs(data.change)}%</span>
                        </div>
                    ` : ''}
                </div>
            `;
        },

        // Render link preview
        renderLinkPreview: function(link) {
            const shortUrl = `${window.location.origin}/r/${link.short_code}`;
            
            return `
                <div class="tf-link-preview">
                    <div class="short-url">
                        <input type="text" value="${shortUrl}" readonly id="link-${link.name}">
                        <button class="btn-copy" onclick="TrackFlow.utils.copyToClipboard('${shortUrl}')">
                            <i class="fa fa-copy"></i> Copy
                        </button>
                    </div>
                    <div class="destination">
                        <i class="fa fa-external-link"></i> ${link.destination_url}
                    </div>
                    ${link.qr_code ? `
                        <div class="tf-qr-code" id="qr-${link.name}"></div>
                    ` : ''}
                </div>
            `;
        }
    };

    // Chart functions
    TrackFlow.charts = {
        // Initialize chart defaults
        init: function() {
            if (typeof Chart !== 'undefined') {
                Chart.defaults.global.defaultFontFamily = 'Inter, system-ui, sans-serif';
                Chart.defaults.global.defaultFontColor = '#5f6368';
            }
        },

        // Render line chart
        renderLineChart: function(container, data, options = {}) {
            const ctx = $(container)[0].getContext('2d');
            
            const defaults = {
                type: 'line',
                data: data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        yAxes: [{
                            ticks: {
                                beginAtZero: true
                            }
                        }]
                    },
                    legend: {
                        display: true,
                        position: 'bottom'
                    }
                }
            };
            
            const config = $.extend(true, defaults, options);
            return new Chart(ctx, config);
        },

        // Render bar chart
        renderBarChart: function(container, data, options = {}) {
            const ctx = $(container)[0].getContext('2d');
            
            const defaults = {
                type: 'bar',
                data: data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        yAxes: [{
                            ticks: {
                                beginAtZero: true
                            }
                        }]
                    }
                }
            };
            
            const config = $.extend(true, defaults, options);
            return new Chart(ctx, config);
        },

        // Render doughnut chart
        renderDoughnutChart: function(container, data, options = {}) {
            const ctx = $(container)[0].getContext('2d');
            
            const defaults = {
                type: 'doughnut',
                data: data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    legend: {
                        position: 'right'
                    }
                }
            };
            
            const config = $.extend(true, defaults, options);
            return new Chart(ctx, config);
        }
    };

    // UTM Builder
    TrackFlow.utmBuilder = {
        // Build UTM URL
        buildUrl: function(baseUrl, params) {
            const url = new URL(baseUrl);
            
            // Add UTM parameters
            Object.keys(params).forEach(key => {
                if (params[key]) {
                    url.searchParams.set(key, params[key]);
                }
            });
            
            return url.toString();
        },

        // Validate UTM parameters
        validateParams: function(params) {
            const required = ['utm_source', 'utm_medium', 'utm_campaign'];
            const missing = [];
            
            required.forEach(param => {
                if (!params[param]) {
                    missing.push(param);
                }
            });
            
            return {
                valid: missing.length === 0,
                missing: missing
            };
        },

        // Generate UTM preview
        generatePreview: function(baseUrl, params) {
            const validation = this.validateParams(params);
            
            if (!validation.valid) {
                return {
                    error: `Missing required parameters: ${validation.missing.join(', ')}`
                };
            }
            
            return {
                url: this.buildUrl(baseUrl, params),
                params: params
            };
        }
    };

    // Real-time updates
    TrackFlow.realtime = {
        intervals: {},

        // Start real-time updates
        start: function(key, callback, interval) {
            this.stop(key);
            this.intervals[key] = setInterval(callback, interval || TrackFlow.config.refreshInterval);
            callback(); // Run immediately
        },

        // Stop real-time updates
        stop: function(key) {
            if (this.intervals[key]) {
                clearInterval(this.intervals[key]);
                delete this.intervals[key];
            }
        },

        // Stop all intervals
        stopAll: function() {
            Object.keys(this.intervals).forEach(key => this.stop(key));
        }
    };

    // Initialize
    $(document).ready(function() {
        TrackFlow.charts.init();
        
        // Stop all intervals when page is hidden
        document.addEventListener('visibilitychange', function() {
            if (document.hidden) {
                TrackFlow.realtime.stopAll();
            }
        });
    });

    // Expose to global scope
    window.TrackFlow = TrackFlow;

})(window.TrackFlow);
