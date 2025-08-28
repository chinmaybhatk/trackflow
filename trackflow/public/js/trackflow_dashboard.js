frappe.provide("trackflow");

trackflow.Dashboard = class TrackFlowDashboard {
    constructor(wrapper) {
        this.wrapper = wrapper;
        this.make();
    }

    make() {
        this.wrapper.html(`
            <div class="trackflow-dashboard">
                <div class="page-head">
                    <div class="page-head-content">
                        <div class="page-title">
                            <h1 class="page-title-text">TrackFlow Analytics</h1>
                        </div>
                    </div>
                </div>
                
                <div class="trackflow-filters row mb-4">
                    <div class="col-md-3">
                        <select class="form-control" id="period-filter">
                            <option value="today">Today</option>
                            <option value="7days" selected>Last 7 Days</option>
                            <option value="30days">Last 30 Days</option>
                            <option value="90days">Last 90 Days</option>
                        </select>
                    </div>
                    <div class="col-md-3">
                        <button class="btn btn-primary btn-sm" id="refresh-btn">
                            <i class="fa fa-refresh"></i> Refresh
                        </button>
                    </div>
                </div>
                
                <div class="trackflow-metrics row">
                    <div class="col-md-3">
                        <div class="metric-card">
                            <div class="metric-value" id="total-clicks">-</div>
                            <div class="metric-label">Total Clicks</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="metric-card">
                            <div class="metric-value" id="unique-visitors">-</div>
                            <div class="metric-label">Unique Visitors</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="metric-card">
                            <div class="metric-value" id="conversions">-</div>
                            <div class="metric-label">Conversions</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="metric-card">
                            <div class="metric-value" id="conversion-rate">-</div>
                            <div class="metric-label">Conversion Rate</div>
                        </div>
                    </div>
                </div>
                
                <div class="row mt-4">
                    <div class="col-md-6">
                        <div class="dashboard-card">
                            <h4>Traffic Trend</h4>
                            <div id="traffic-chart"></div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="dashboard-card">
                            <h4>Top Campaigns</h4>
                            <div id="campaigns-table"></div>
                        </div>
                    </div>
                </div>
                
                <div class="row mt-4">
                    <div class="col-md-6">
                        <div class="dashboard-card">
                            <h4>Traffic Sources</h4>
                            <div id="sources-chart"></div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="dashboard-card">
                            <h4>Recent Conversions</h4>
                            <div id="conversions-list"></div>
                        </div>
                    </div>
                </div>
            </div>
        `);
        
        this.setup_events();
        this.refresh_dashboard();
    }
    
    setup_events() {
        this.wrapper.find('#refresh-btn').on('click', () => {
            this.refresh_dashboard();
        });
        
        this.wrapper.find('#period-filter').on('change', () => {
            this.refresh_dashboard();
        });
    }
    
    refresh_dashboard() {
        const period = this.wrapper.find('#period-filter').val();
        
        frappe.call({
            method: 'trackflow.api.analytics.get_analytics',
            args: { period: period },
            callback: (r) => {
                if (r.message) {
                    this.render_metrics(r.message);
                    this.render_charts(r.message);
                    this.render_campaigns(r.message.campaigns);
                }
            }
        });
    }
    
    render_metrics(data) {
        this.wrapper.find('#total-clicks').text(data.traffic.total_clicks || 0);
        this.wrapper.find('#unique-visitors').text(data.traffic.unique_visitors || 0);
        this.wrapper.find('#conversions').text(data.conversions.total_conversions || 0);
        this.wrapper.find('#conversion-rate').text(
            (data.conversions.conversion_rate || 0).toFixed(2) + '%'
        );
    }
    
    render_charts(data) {
        // Traffic trend chart
        if (data.timeseries && data.timeseries.length) {
            const chart_data = {
                labels: data.timeseries.map(d => d.date),
                datasets: [{
                    name: "Clicks",
                    values: data.timeseries.map(d => d.clicks)
                }, {
                    name: "Conversions",
                    values: data.timeseries.map(d => d.conversions || 0)
                }]
            };
            
            new frappe.Chart('#traffic-chart', {
                data: chart_data,
                type: 'line',
                height: 250,
                colors: ['#2490ef', '#00c853']
            });
        }
        
        // Sources pie chart
        if (data.sources && data.sources.length) {
            const source_data = {
                labels: data.sources.slice(0, 5).map(s => s.source),
                datasets: [{
                    values: data.sources.slice(0, 5).map(s => s.clicks)
                }]
            };
            
            new frappe.Chart('#sources-chart', {
                data: source_data,
                type: 'pie',
                height: 250
            });
        }
    }
    
    render_campaigns(campaigns) {
        if (!campaigns || !campaigns.length) {
            this.wrapper.find('#campaigns-table').html('<p>No campaigns found</p>');
            return;
        }
        
        let html = `
            <table class="table table-sm">
                <thead>
                    <tr>
                        <th>Campaign</th>
                        <th>Clicks</th>
                        <th>Conversions</th>
                        <th>Revenue</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        campaigns.slice(0, 5).forEach(c => {
            html += `
                <tr>
                    <td>${c.campaign}</td>
                    <td>${c.clicks}</td>
                    <td>${c.conversions}</td>
                    <td>${format_currency(c.revenue)}</td>
                </tr>
            `;
        });
        
        html += '</tbody></table>';
        this.wrapper.find('#campaigns-table').html(html);
    }
}

// Add to CRM sidebar
$(document).on('app_ready', function() {
    if (frappe.get_route()[0] === 'crm') {
        // Add TrackFlow to CRM menu
        frappe.ui.toolbar.add_dropdown_item({
            label: 'TrackFlow Analytics',
            action: function() {
                frappe.set_route('trackflow-dashboard');
            },
            standard: true
        });
    }
});

// Page route
frappe.pages['trackflow-dashboard'] = {
    start: function(wrapper) {
        new trackflow.Dashboard(wrapper);
    }
};
