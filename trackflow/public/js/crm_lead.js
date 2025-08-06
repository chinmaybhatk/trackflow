frappe.ui.form.on('CRM Lead', {
    refresh: function(frm) {
        // Add TrackFlow section
        add_trackflow_section(frm);
        
        // Show tracking data if available
        if (frm.doc.trackflow_visitor_id) {
            show_tracking_summary(frm);
            add_view_journey_button(frm);
        }
        
        // Add tracking indicator
        if (frm.doc.trackflow_source) {
            frm.add_custom_button(__('View Attribution'), function() {
                show_lead_attribution(frm);
            }, __('TrackFlow'));
        }
    },
    
    onload: function(frm) {
        // Set tracking data from URL parameters if creating from tracked link
        if (frm.is_new() && frappe.route_options) {
            set_tracking_from_route(frm);
        }
    }
});

function add_trackflow_section(frm) {
    // Add custom HTML section for TrackFlow data
    if (!frm.fields_dict.trackflow_html) {
        frm.add_custom_button(__('TrackFlow Dashboard'), function() {
            frappe.set_route('trackflow-dashboard');
        }, __('TrackFlow'));
    }
}

function show_tracking_summary(frm) {
    frappe.call({
        method: 'trackflow.integrations.crm_lead.get_lead_source_data',
        args: {
            lead_name: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                let html = build_tracking_summary_html(r.message);
                
                // Add to form
                frm.set_df_property('trackflow_source', 'description', html);
            }
        }
    });
}

function build_tracking_summary_html(data) {
    let html = `
        <div class="trackflow-summary">
            <h4>Tracking Summary</h4>
            <div class="row">
                <div class="col-md-6">
                    <p><strong>Source:</strong> ${data.source || 'Direct'}</p>
                    <p><strong>Medium:</strong> ${data.medium || 'None'}</p>
                    <p><strong>Campaign:</strong> ${data.campaign || 'None'}</p>
                </div>
                <div class="col-md-6">
                    <p><strong>First Touch:</strong> ${data.first_touch || 'N/A'}</p>
                    <p><strong>Last Touch:</strong> ${data.last_touch || 'N/A'}</p>
                    <p><strong>Total Touches:</strong> ${data.touch_count || 0}</p>
                </div>
            </div>
        </div>
    `;
    
    return html;
}

function add_view_journey_button(frm) {
    frm.add_custom_button(__('View Journey'), function() {
        show_visitor_journey(frm);
    }, __('TrackFlow'));
}

function show_visitor_journey(frm) {
    frappe.call({
        method: 'trackflow.integrations.crm_lead.get_lead_source_data',
        args: {
            lead_name: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.visitor_journey) {
                show_journey_dialog(r.message.visitor_journey);
            }
        }
    });
}

function show_journey_dialog(journey) {
    let journey_html = '<div class="visitor-journey">';
    
    journey.forEach(function(event) {
        journey_html += `
            <div class="journey-event">
                <div class="event-time">${event.timestamp}</div>
                <div class="event-type">${event.type}</div>
                <div class="event-details">${JSON.stringify(event.data)}</div>
            </div>
        `;
    });
    
    journey_html += '</div>';
    
    let d = new frappe.ui.Dialog({
        title: __('Visitor Journey'),
        fields: [{
            fieldtype: 'HTML',
            fieldname: 'journey_html',
            options: journey_html
        }],
        size: 'large'
    });
    
    d.show();
}

function show_lead_attribution(frm) {
    let attribution_html = `
        <div class="lead-attribution">
            <h4>Lead Attribution</h4>
            <table class="table table-bordered">
                <thead>
                    <tr>
                        <th>Attribute</th>
                        <th>Value</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Source</td>
                        <td>${frm.doc.trackflow_source || 'Direct'}</td>
                    </tr>
                    <tr>
                        <td>Medium</td>
                        <td>${frm.doc.trackflow_medium || 'None'}</td>
                    </tr>
                    <tr>
                        <td>Campaign</td>
                        <td>${frm.doc.trackflow_campaign || 'None'}</td>
                    </tr>
                    <tr>
                        <td>First Touch Date</td>
                        <td>${frm.doc.trackflow_first_touch_date || 'N/A'}</td>
                    </tr>
                    <tr>
                        <td>Last Touch Date</td>
                        <td>${frm.doc.trackflow_last_touch_date || 'N/A'}</td>
                    </tr>
                    <tr>
                        <td>Touch Count</td>
                        <td>${frm.doc.trackflow_touch_count || 0}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    `;
    
    frappe.msgprint({
        title: __('Lead Attribution Details'),
        message: attribution_html,
        indicator: 'blue'
    });
}

function set_tracking_from_route(frm) {
    // Set tracking fields from route options (when creating from web form)
    if (frappe.route_options.trackflow_source) {
        frm.set_value('trackflow_source', frappe.route_options.trackflow_source);
    }
    if (frappe.route_options.trackflow_medium) {
        frm.set_value('trackflow_medium', frappe.route_options.trackflow_medium);
    }
    if (frappe.route_options.trackflow_campaign) {
        frm.set_value('trackflow_campaign', frappe.route_options.trackflow_campaign);
    }
    if (frappe.route_options.trackflow_visitor_id) {
        frm.set_value('trackflow_visitor_id', frappe.route_options.trackflow_visitor_id);
    }
}

// Add custom CSS for TrackFlow elements
frappe.ui.form.on('CRM Lead', {
    onload_post_render: function(frm) {
        $('<style>')
            .prop('type', 'text/css')
            .html(`
                .trackflow-summary {
                    background: #f5f5f5;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 10px 0;
                }
                .visitor-journey {
                    max-height: 400px;
                    overflow-y: auto;
                }
                .journey-event {
                    border-bottom: 1px solid #e0e0e0;
                    padding: 10px;
                }
                .event-time {
                    font-size: 12px;
                    color: #666;
                }
                .event-type {
                    font-weight: bold;
                    color: #333;
                }
                .event-details {
                    font-size: 11px;
                    color: #666;
                    margin-top: 5px;
                }
            `)
            .appendTo('head');
    }
});
