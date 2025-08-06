frappe.ui.form.on('CRM Organization', {
    refresh: function(frm) {
        // Add TrackFlow engagement dashboard
        if (!frm.is_new()) {
            add_engagement_dashboard(frm);
            
            // Add tracking summary button
            frm.add_custom_button(__('Tracking Summary'), function() {
                show_tracking_summary(frm);
            }, __('TrackFlow'));
            
            // Add engagement timeline button
            if (frm.doc.trackflow_visitor_id) {
                frm.add_custom_button(__('View Timeline'), function() {
                    show_engagement_timeline(frm);
                }, __('TrackFlow'));
            }
        }
        
        // Auto-link leads based on domain
        if (frm.doc.website && !frm.doc.trackflow_visitor_id) {
            check_and_link_leads(frm);
        }
    },
    
    website: function(frm) {
        // Check for matching leads when website is entered
        if (frm.doc.website) {
            check_and_link_leads(frm);
        }
    },
    
    after_save: function(frm) {
        // Update engagement score after save
        update_engagement_score(frm);
    }
});

function add_engagement_dashboard(frm) {
    // Create engagement dashboard HTML
    let dashboard_html = `
        <div class="engagement-dashboard">
            <h4>Organization Engagement</h4>
            <div class="row">
                <div class="col-md-3">
                    <div class="engagement-card">
                        <div class="card-label">Engagement Score</div>
                        <div class="card-value">${frm.doc.trackflow_engagement_score || 0}</div>
                        <div class="card-trend">${get_score_trend(frm.doc.trackflow_engagement_score)}</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="engagement-card">
                        <div class="card-label">Last Campaign</div>
                        <div class="card-value">${frm.doc.trackflow_last_campaign || 'None'}</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="engagement-card" id="total-leads-card">
                        <div class="card-label">Total Leads</div>
                        <div class="card-value">-</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="engagement-card" id="total-deals-card">
                        <div class="card-label">Total Deals</div>
                        <div class="card-value">-</div>
                    </div>
                </div>
            </div>
            <div class="engagement-chart-container">
                <div id="engagement-activity-chart"></div>
            </div>
        </div>
    `;
    
    // Add to form
    if (!frm.fields_dict.engagement_dashboard_html) {
        frm.add_field({
            fieldname: 'engagement_dashboard_html',
            fieldtype: 'HTML',
            options: dashboard_html
        });
    } else {
        frm.fields_dict.engagement_dashboard_html.$wrapper.html(dashboard_html);
    }
    
    // Load engagement data
    load_engagement_metrics(frm);
}

function get_score_trend(score) {
    if (score >= 100) {
        return '<i class="fa fa-arrow-up text-success"></i> High';
    } else if (score >= 50) {
        return '<i class="fa fa-minus text-warning"></i> Medium';
    } else {
        return '<i class="fa fa-arrow-down text-danger"></i> Low';
    }
}

function load_engagement_metrics(frm) {
    frappe.call({
        method: 'trackflow.integrations.crm_organization.get_organization_tracking_summary',
        args: {
            organization_name: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                // Update metrics
                $('#total-leads-card .card-value').text(r.message.total_leads);
                $('#total-deals-card .card-value').text(r.message.total_deals);
                
                // Render activity chart if data available
                if (r.message.recent_activity && r.message.recent_activity.length > 0) {
                    render_activity_chart(r.message.recent_activity);
                }
                
                // Store data for later use
                frm.tracking_summary = r.message;
            }
        }
    });
}

function render_activity_chart(activity_data) {
    // Group activity by date
    let activity_by_date = {};
    
    activity_data.forEach(function(event) {
        let date = frappe.datetime.str_to_user(event.timestamp).split(' ')[0];
        activity_by_date[date] = (activity_by_date[date] || 0) + 1;
    });
    
    // Prepare chart data
    let dates = Object.keys(activity_by_date).sort();
    let values = dates.map(date => activity_by_date[date]);
    
    // Render chart
    new frappe.Chart('#engagement-activity-chart', {
        data: {
            labels: dates,
            datasets: [{
                name: 'Activity',
                values: values
            }]
        },
        type: 'bar',
        height: 200,
        colors: ['#2563eb'],
        axisOptions: {
            xAxisMode: 'tick'
        }
    });
}

function check_and_link_leads(frm) {
    frappe.call({
        method: 'trackflow.integrations.crm_organization.link_organization_to_leads',
        args: {
            organization: frm.doc
        },
        callback: function(r) {
            if (r.message) {
                frappe.msgprint(__('Linked {0} leads to this organization', [r.message]));
                frm.reload_doc();
            }
        }
    });
}

function show_tracking_summary(frm) {
    if (frm.tracking_summary) {
        show_summary_dialog(frm.tracking_summary);
    } else {
        frappe.call({
            method: 'trackflow.integrations.crm_organization.get_organization_tracking_summary',
            args: {
                organization_name: frm.doc.name
            },
            callback: function(r) {
                if (r.message) {
                    show_summary_dialog(r.message);
                }
            }
        });
    }
}

function show_summary_dialog(summary_data) {
    let summary_html = build_summary_html(summary_data);
    
    let d = new frappe.ui.Dialog({
        title: __('Organization Tracking Summary'),
        fields: [{
            fieldtype: 'HTML',
            fieldname: 'summary_html',
            options: summary_html
        }],
        size: 'large',
        primary_action_label: __('Export'),
        primary_action: function() {
            export_tracking_summary(summary_data);
        }
    });
    
    d.show();
}

function build_summary_html(data) {
    // Build leads table
    let leads_html = '';
    if (data.leads && data.leads.length > 0) {
        data.leads.forEach(function(lead) {
            leads_html += `
                <tr>
                    <td><a href="/app/crm-lead/${lead.name}">${lead.lead_name}</a></td>
                    <td>${lead.status}</td>
                    <td>${lead.trackflow_source || 'Direct'}</td>
                    <td>${lead.trackflow_campaign || 'None'}</td>
                </tr>
            `;
        });
    }
    
    // Build deals table
    let deals_html = '';
    if (data.deals && data.deals.length > 0) {
        data.deals.forEach(function(deal) {
            deals_html += `
                <tr>
                    <td><a href="/app/crm-deal/${deal.name}">${deal.deal_name}</a></td>
                    <td>${deal.stage}</td>
                    <td>${format_currency(deal.annual_revenue)}</td>
                </tr>
            `;
        });
    }
    
    // Build campaign influence
    let campaigns_html = '';
    if (data.campaign_influence) {
        Object.keys(data.campaign_influence).forEach(function(campaign) {
            campaigns_html += `
                <tr>
                    <td>${campaign}</td>
                    <td>${data.campaign_influence[campaign]} leads</td>
                </tr>
            `;
        });
    }
    
    return `
        <div class="tracking-summary">
            <div class="summary-header">
                <div class="row">
                    <div class="col-md-4">
                        <p><strong>Engagement Score:</strong> ${data.engagement_score}</p>
                        <p><strong>First Seen:</strong> ${data.first_seen || 'N/A'}</p>
                    </div>
                    <div class="col-md-4">
                        <p><strong>Total Leads:</strong> ${data.total_leads}</p>
                        <p><strong>Total Deals:</strong> ${data.total_deals}</p>
                    </div>
                    <div class="col-md-4">
                        <p><strong>Deal Value:</strong> ${format_currency(data.total_deal_value)}</p>
                        <p><strong>Last Seen:</strong> ${data.last_seen || 'N/A'}</p>
                    </div>
                </div>
            </div>
            
            <div class="summary-section">
                <h5>Associated Leads</h5>
                <table class="table table-condensed">
                    <thead>
                        <tr>
                            <th>Lead Name</th>
                            <th>Status</th>
                            <th>Source</th>
                            <th>Campaign</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${leads_html || '<tr><td colspan="4">No leads found</td></tr>'}
                    </tbody>
                </table>
            </div>
            
            <div class="summary-section">
                <h5>Associated Deals</h5>
                <table class="table table-condensed">
                    <thead>
                        <tr>
                            <th>Deal Name</th>
                            <th>Stage</th>
                            <th>Value</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${deals_html || '<tr><td colspan="3">No deals found</td></tr>'}
                    </tbody>
                </table>
            </div>
            
            <div class="summary-section">
                <h5>Campaign Influence</h5>
                <table class="table table-condensed">
                    <thead>
                        <tr>
                            <th>Campaign</th>
                            <th>Influence</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${campaigns_html || '<tr><td colspan="2">No campaign data</td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>
    `;
}

function show_engagement_timeline(frm) {
    frappe.call({
        method: 'trackflow.api.visitor.get_visitor_timeline',
        args: {
            visitor_id: frm.doc.trackflow_visitor_id
        },
        callback: function(r) {
            if (r.message) {
                show_timeline_dialog(r.message);
            }
        }
    });
}

function show_timeline_dialog(timeline_data) {
    let timeline_html = build_timeline_html(timeline_data);
    
    let d = new frappe.ui.Dialog({
        title: __('Organization Engagement Timeline'),
        fields: [{
            fieldtype: 'HTML',
            fieldname: 'timeline_html',
            options: timeline_html
        }],
        size: 'large'
    });
    
    d.show();
}

function build_timeline_html(events) {
    let timeline_html = '<div class="engagement-timeline">';
    
    events.forEach(function(event, idx) {
        timeline_html += `
            <div class="timeline-item">
                <div class="timeline-marker"></div>
                <div class="timeline-content">
                    <div class="timeline-header">
                        <span class="timeline-date">${frappe.datetime.str_to_user(event.timestamp)}</span>
                        <span class="timeline-type badge badge-primary">${event.event_type}</span>
                    </div>
                    <div class="timeline-body">
                        ${format_event_details(event)}
                    </div>
                </div>
            </div>
        `;
    });
    
    timeline_html += '</div>';
    return timeline_html;
}

function format_event_details(event) {
    let details = JSON.parse(event.event_data || '{}');
    let html = '';
    
    switch(event.event_type) {
        case 'page_view':
            html = `Visited page: ${details.page || 'Unknown'}`;
            break;
        case 'form_submission':
            html = `Submitted form: ${details.form_name || 'Unknown'}`;
            break;
        case 'lead_created':
            html = `Lead created: <a href="/app/crm-lead/${details.lead}">${details.lead_name}</a>`;
            break;
        case 'deal_created':
            html = `Deal created: <a href="/app/crm-deal/${details.deal}">${details.deal_name}</a>`;
            break;
        default:
            html = `${event.event_type}: ${JSON.stringify(details)}`;
    }
    
    return html;
}

function update_engagement_score(frm) {
    frappe.call({
        method: 'trackflow.integrations.crm_organization.update_organization_engagement',
        args: {
            organization: frm.doc
        },
        callback: function(r) {
            if (r.message) {
                frm.reload_doc();
            }
        }
    });
}

function export_tracking_summary(summary_data) {
    // Generate CSV export
    frappe.call({
        method: 'trackflow.api.exports.export_organization_summary',
        args: {
            summary_data: summary_data
        },
        callback: function(r) {
            if (r.message) {
                window.open(r.message);
            }
        }
    });
}

function format_currency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount || 0);
}

// Add custom CSS
frappe.ui.form.on('CRM Organization', {
    onload_post_render: function(frm) {
        $('<style>')
            .prop('type', 'text/css')
            .html(`
                .engagement-dashboard {
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 15px 0;
                }
                .engagement-card {
                    background: white;
                    padding: 20px;
                    border-radius: 5px;
                    text-align: center;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }
                .card-label {
                    font-size: 12px;
                    color: #666;
                    text-transform: uppercase;
                }
                .card-value {
                    font-size: 24px;
                    font-weight: bold;
                    color: #333;
                    margin: 10px 0;
                }
                .card-trend {
                    font-size: 14px;
                }
                .engagement-chart-container {
                    margin-top: 20px;
                    background: white;
                    padding: 15px;
                    border-radius: 5px;
                }
                .tracking-summary {
                    padding: 15px;
                }
                .summary-header {
                    background: #e3f2fd;
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }
                .summary-section {
                    margin: 20px 0;
                }
                .engagement-timeline {
                    position: relative;
                    padding: 20px 0;
                }
                .timeline-item {
                    position: relative;
                    padding-left: 40px;
                    margin-bottom: 20px;
                }
                .timeline-marker {
                    position: absolute;
                    left: 10px;
                    top: 5px;
                    width: 10px;
                    height: 10px;
                    background: #2563eb;
                    border-radius: 50%;
                }
                .timeline-item:not(:last-child)::before {
                    content: '';
                    position: absolute;
                    left: 14px;
                    top: 15px;
                    bottom: -20px;
                    width: 2px;
                    background: #e0e0e0;
                }
                .timeline-content {
                    background: white;
                    padding: 15px;
                    border-radius: 5px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }
                .timeline-header {
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 10px;
                }
                .timeline-date {
                    font-size: 12px;
                    color: #666;
                }
            `)
            .appendTo('head');
    }
});
