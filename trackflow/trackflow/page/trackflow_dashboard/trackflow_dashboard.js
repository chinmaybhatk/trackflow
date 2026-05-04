frappe.pages['trackflow-dashboard'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'TrackFlow Dashboard',
        single_column: true
    });

    // Add custom CSS class
    page.wrapper.addClass('trackflow-dashboard-page');

    // Create dashboard instance
    new TrackFlowDashboard(page);
};

class TrackFlowDashboard {
    constructor(page) {
        this.page = page;
        this.filters = {};
        this.charts = {};
        this.data = {};
        
        this.setup_page();
        this.setup_filters();
        this.setup_layout();
        this.refresh_dashboard();
        
        // Auto-refresh every 5 minutes
        setInterval(() => this.refresh_dashboard(), 300000);
    }

    setup_page() {
        // Add refresh button
        this.page.set_primary_action(__('Refresh'), () => {
            this.refresh_dashboard();
        }, 'octicon octicon-sync');

        // Add export button
        this.page.set_secondary_action(__('Export'), () => {
            this.export_data();
        }, 'octicon octicon-download');
    }

    setup_filters() {
        // Date range filter
        this.date_range = this.page.add_field({
            label: __('Date Range'),
            fieldtype: 'Select',
            fieldname: 'date_range',
            options: [
                'Last 7 Days',
                'Last 30 Days',
                'Last 3 Months',
                'Last 6 Months',
                'Last Year',
                'Custom'
            ],
            default: 'Last 30 Days',
            change: () => this.handle_date_range_change()
        });

        // Campaign filter
        this.campaign_filter = this.page.add_field({
            label: __('Campaign'),
            fieldtype: 'Link',
            fieldname: 'campaign',
            options: 'Link Campaign',
            change: () => this.refresh_dashboard()
        });

        // Source filter
        this.source_filter = this.page.add_field({
            label: __('Source'),
            fieldtype: 'Data',
            fieldname: 'source',
            change: () => this.refresh_dashboard()
        });
    }

    handle_date_range_change() {
        const range = this.date_range.get_value();
        if (range === 'Custom') {
            this.show_custom_date_dialog();
        } else {
            this.refresh_dashboard();
        }
    }

    show_custom_date_dialog() {
        const dialog = new frappe.ui.Dialog({
            title: __('Select Date Range'),
            fields: [
                {
                    label: __('From Date'),
                    fieldname: 'from_date',
                    fieldtype: 'Date',
                    default: frappe.datetime.add_days(frappe.datetime.get_today(), -30),
                    reqd: 1
                },
                {
                    label: __('To Date'),
                    fieldname: 'to_date',
                    fieldtype: 'Date',
                    default: frappe.datetime.get_today(),
                    reqd: 1
                }
            ],
            primary_action_label: __('Apply'),
            primary_action: (values) => {
                this.filters.from_date = values.from_date;
                this.filters.to_date = values.to_date;
                this.refresh_dashboard();
                dialog.hide();
            }
        });
        dialog.show();
    }

    setup_layout() {
        // Clear existing content
        this.page.main.empty();

        // Create main container
        this.container = $(`
            <div class="trackflow-dashboard">
                <!-- Summary Cards -->
                <div class="dashboard-summary">
                    <div class="row"></div>
                </div>

                <!-- Charts Row 1 -->
                <div class="dashboard-charts-row-1">
                    <div class="row">
                        <div class="col-md-8">
                            <div class="dashboard-card">
                                <h4>${__('Conversion Trend')}</h4>
                                <div id="visitor-trend-chart"></div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="dashboard-card">
                                <h4>${__('Traffic Sources')}</h4>
                                <div id="source-chart"></div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Conversion Funnel (full width) -->
                <div class="dashboard-charts-row-2">
                    <div class="row">
                        <div class="col-md-12">
                            <div class="dashboard-card">
                                <h4>${__('Conversion Funnel')}</h4>
                                <div id="funnel-chart"></div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Campaign Performance Table -->
                <div class="dashboard-campaigns">
                    <div class="dashboard-card">
                        <h4>${__('Campaign Performance')}</h4>
                        <div id="campaign-table"></div>
                    </div>
                </div>

                <!-- Recent Visitors -->
                <div class="dashboard-visitors">
                    <div class="dashboard-card">
                        <h4>${__('Recent Visitors')}</h4>
                        <div id="visitor-table"></div>
                    </div>
                </div>
            </div>
        `).appendTo(this.page.main);
    }

    refresh_dashboard() {
        // Show loading state
        frappe.show_progress(__('Loading Dashboard'), 70);

        // Get date range
        const date_range = this.get_date_range();
        
        // Build filters
        const filters = {
            ...date_range,
            campaign: this.campaign_filter.get_value(),
            source: this.source_filter.get_value()
        };

        // Fetch dashboard data
        frappe.call({
            method: 'trackflow.trackflow.page.trackflow_dashboard.trackflow_dashboard.get_dashboard_data',
            args: filters,
            callback: (r) => {
                if (r.message) {
                    this.data = r.message;
                    this.render_dashboard();
                }
                frappe.hide_progress();
            },
            error: () => {
                frappe.hide_progress();
                frappe.msgprint(__('Failed to load dashboard data'));
            }
        });
    }

    get_date_range() {
        const range = this.date_range.get_value();
        let from_date, to_date;

        if (this.filters.from_date && this.filters.to_date && range === 'Custom') {
            return {
                from_date: this.filters.from_date,
                to_date: this.filters.to_date
            };
        }

        to_date = frappe.datetime.get_today();

        switch(range) {
            case 'Last 7 Days':
                from_date = frappe.datetime.add_days(to_date, -7);
                break;
            case 'Last 30 Days':
                from_date = frappe.datetime.add_days(to_date, -30);
                break;
            case 'Last 3 Months':
                from_date = frappe.datetime.add_months(to_date, -3);
                break;
            case 'Last 6 Months':
                from_date = frappe.datetime.add_months(to_date, -6);
                break;
            case 'Last Year':
                from_date = frappe.datetime.add_months(to_date, -12);
                break;
            default:
                from_date = frappe.datetime.add_days(to_date, -30);
        }

        return { from_date, to_date };
    }

    render_dashboard() {
        this.render_summary_cards();
        this.render_visitor_trend_chart();
        this.render_source_chart();
        this.render_funnel_chart();
        this.render_campaign_table();
        this.render_visitor_table();
    }

    render_summary_cards() {
        const summary = this.data.summary || {};

        // Build a card with a real period-over-period delta indicator.
        // delta is null when there is no prior-window baseline.
        const card = (value, label, delta) => {
            let indicator = '';
            if (delta === null || delta === undefined) {
                indicator = `<div class="card-indicator neutral">—</div>`;
            } else if (delta > 0) {
                indicator = `<div class="card-indicator positive">+${delta}%</div>`;
            } else if (delta < 0) {
                indicator = `<div class="card-indicator negative">${delta}%</div>`;
            } else {
                indicator = `<div class="card-indicator neutral">0%</div>`;
            }
            return `
                <div class="col-sm-6 col-lg-2">
                    <div class="summary-card">
                        <div class="card-value">${value}</div>
                        <div class="card-label">${label}</div>
                        ${indicator}
                    </div>
                </div>`;
        };

        const cards_html = [
            card(format_number(summary.total_visitors || 0), __('Total Visitors'),
                 summary.visitors_delta),
            card(format_number(summary.total_sessions || 0), __('Sessions'),
                 summary.sessions_delta),
            card(format_number(summary.total_page_views || 0), __('Page Views'),
                 summary.page_views_delta),
            card(`${summary.conversion_rate || 0}%`, __('Conversion Rate'),
                 summary.rate_delta),
            card(format_number(summary.total_conversions || 0), __('Conversions'),
                 summary.conversions_delta),
            card(format_duration(summary.avg_session_duration || 0), __('Avg Duration'),
                 null),
        ].join('');

        this.container.find('.dashboard-summary .row').html(cards_html);
    }

    render_visitor_trend_chart() {
        const conversions = this.data.conversions || [];
        
        // Prepare data for chart
        const dates = conversions.map(d => d.date);
        const visitors = conversions.map(d => d.total || 0);
        const values = conversions.map(d => d.value || 0);

        this.charts.visitor_trend = new frappe.Chart('#visitor-trend-chart', {
            data: {
                labels: dates,
                datasets: [
                    {
                        name: __('Conversions'),
                        values: visitors,
                        chartType: 'line'
                    },
                    {
                        name: __('Value'),
                        values: values,
                        chartType: 'bar'
                    }
                ]
            },
            type: 'axis-mixed',
            height: 300,
            colors: ['#7cd6fd', '#743ee2'],
            axisOptions: {
                xAxisMode: 'tick',
                xIsSeries: true
            },
            barOptions: {
                spaceRatio: 0.5
            },
            tooltipOptions: {
                formatTooltipX: d => frappe.datetime.str_to_user(d),
                formatTooltipY: d => format_currency(d)
            }
        });
    }

    render_source_chart() {
        const sources = this.data.sources || [];
        
        // Prepare data for pie chart
        const labels = sources.map(s => s.source || 'Direct');
        const data = sources.map(s => s.visitors || 0);

        this.charts.source = new frappe.Chart('#source-chart', {
            data: {
                labels: labels,
                datasets: [{
                    values: data
                }]
            },
            type: 'pie',
            height: 300,
            colors: ['#7cd6fd', '#5e64ff', '#743ee2', '#ff5858', '#ffa00a', '#28a745']
        });
    }

    render_funnel_chart() {
        // Site-wide funnel built from real summary metrics, not campaign
        // aggregates (which collapse to 0 when there are no Active campaigns).
        const summary = this.data.summary || {};
        const stages = [
            { label: __('Unique Visitors'),  value: summary.total_visitors    || 0 },
            { label: __('Clicks Tracked'),   value: summary.total_sessions    || 0 },
            { label: __('Conversions'),      value: summary.total_conversions || 0 },
        ];

        const top = Math.max(stages[0].value, 1); // avoid divide-by-zero
        const funnel_html = stages.map((stage) => {
            const pct = (stage.value / top * 100).toFixed(1);
            return `
                <div class="funnel-stage">
                    <div class="funnel-bar" style="width: ${pct}%;">
                        <span class="funnel-label">${stage.label}</span>
                        <span class="funnel-value">${format_number(stage.value)} (${pct}%)</span>
                    </div>
                </div>
            `;
        }).join('');

        $('#funnel-chart').html(`<div class="funnel-container">${funnel_html}</div>`);
    }

    render_campaign_table() {
        const campaigns = this.data.campaigns || [];
        
        if (campaigns.length === 0) {
            $('#campaign-table').html(`<p class="text-muted">${__('No campaign data available')}</p>`);
            return;
        }

        const table_html = `
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>${__('Campaign')}</th>
                        <th>${__('Source')}</th>
                        <th>${__('Medium')}</th>
                        <th class="text-right">${__('Visitors')}</th>
                        <th class="text-right">${__('Conversions')}</th>
                        <th class="text-right">${__('Conv. Rate')}</th>
                        <th class="text-right">${__('Value')}</th>
                    </tr>
                </thead>
                <tbody>
                    ${campaigns.map(campaign => `
                        <tr>
                            <td>
                                <a href="/app/campaign/${campaign.name}">
                                    ${campaign.campaign_name}
                                </a>
                            </td>
                            <td>${campaign.source || '-'}</td>
                            <td>${campaign.medium || '-'}</td>
                            <td class="text-right">${format_number(campaign.visitors)}</td>
                            <td class="text-right">${format_number(campaign.conversions)}</td>
                            <td class="text-right">${campaign.conversion_rate}%</td>
                            <td class="text-right">${format_currency(campaign.total_value)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;

        $('#campaign-table').html(table_html);
    }

    render_visitor_table() {
        const visitors = this.data.recent_visitors || [];
        
        if (visitors.length === 0) {
            $('#visitor-table').html(`<p class="text-muted">${__('No recent visitors')}</p>`);
            return;
        }

        const table_html = `
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>${__('Visitor ID')}</th>
                        <th>${__('First Seen')}</th>
                        <th>${__('Last Seen')}</th>
                        <th>${__('Source')}</th>
                        <th>${__('Campaign')}</th>
                        <th>${__('Location')}</th>
                        <th>${__('Device')}</th>
                        <th class="text-right">${__('Sessions')}</th>
                        <th class="text-right">${__('Page Views')}</th>
                    </tr>
                </thead>
                <tbody>
                    ${visitors.slice(0, 10).map(visitor => `
                        <tr>
                            <td>
                                <a href="/app/visitor/${visitor.name}">
                                    ${visitor.visitor_id.substring(0, 8)}...
                                </a>
                            </td>
                            <td>${frappe.datetime.str_to_user(visitor.first_seen)}</td>
                            <td>${frappe.datetime.str_to_user(visitor.last_seen)}</td>
                            <td>${visitor.utm_source || 'Direct'}</td>
                            <td>${visitor.utm_campaign || '-'}</td>
                            <td>${visitor.city || ''} ${visitor.country || ''}</td>
                            <td>${visitor.device_type || '-'} / ${visitor.browser || '-'}</td>
                            <td class="text-right">${visitor.session_count}</td>
                            <td class="text-right">${visitor.page_view_count}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;

        $('#visitor-table').html(table_html);
    }

    export_data() {
        // Export dashboard data to CSV
        const dialog = new frappe.ui.Dialog({
            title: __('Export Dashboard Data'),
            fields: [
                {
                    label: __('Export Type'),
                    fieldname: 'export_type',
                    fieldtype: 'Select',
                    options: [
                        'Summary Report',
                        'Campaign Performance',
                        'Visitor Details',
                        'Attribution Analysis',
                        'Full Dashboard Data'
                    ],
                    default: 'Summary Report',
                    reqd: 1
                },
                {
                    label: __('Format'),
                    fieldname: 'format',
                    fieldtype: 'Select',
                    options: ['CSV', 'Excel', 'PDF'],
                    default: 'CSV',
                    reqd: 1
                }
            ],
            primary_action_label: __('Export'),
            primary_action: (values) => {
                this.perform_export(values.export_type, values.format);
                dialog.hide();
            }
        });
        dialog.show();
    }

    perform_export(export_type, format) {
        // Prepare data based on export type
        let data_to_export = [];
        let filename = 'trackflow_export';

        switch(export_type) {
            case 'Campaign Performance':
                data_to_export = this.data.campaigns || [];
                filename = 'campaign_performance';
                break;
            case 'Visitor Details':
                data_to_export = this.data.recent_visitors || [];
                filename = 'visitor_details';
                break;
            case 'Attribution Analysis':
                data_to_export = this.data.attribution || [];
                filename = 'attribution_analysis';
                break;
            case 'Full Dashboard Data':
                data_to_export = this.data;
                filename = 'dashboard_full';
                break;
            default:
                data_to_export = [this.data.summary];
                filename = 'summary_report';
        }

        // Convert to CSV and download
        if (format === 'CSV') {
            frappe.tools.downloadify(
                data_to_export,
                null,
                `${filename}_${frappe.datetime.nowdate()}`
            );
        } else {
            frappe.msgprint(__('Export format {0} is not yet implemented', [format]));
        }
    }
}

// Helper functions
function format_number(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

function format_currency(amount) {
    return frappe.format(amount, {fieldtype: 'Currency'});
}

function format_duration(seconds) {
    if (seconds < 60) {
        return seconds + 's';
    } else if (seconds < 3600) {
        return Math.floor(seconds / 60) + 'm ' + (seconds % 60) + 's';
    } else {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return hours + 'h ' + minutes + 'm';
    }
}