frappe.ui.form.on('CRM Lead', {
    refresh: function(frm) {
        // Add TrackFlow buttons
        if (!frm.is_new()) {
            add_trackflow_buttons(frm);
            
            // Show tracking summary if data exists
            if (frm.doc.trackflow_visitor_id || frm.doc.trackflow_source) {
                show_tracking_summary(frm);
            }
        }
    },
    
    onload: function(frm) {
        // Set tracking data from URL parameters if creating from tracked link
        if (frm.is_new() && frappe.route_options && frappe.route_options.trackflow_data) {
            set_tracking_from_route(frm);
        }
    }
});

function add_trackflow_buttons(frm) {
    // Add "Create Tracking Link" button
    frm.add_custom_button(__('Create Tracking Link'), function() {
        create_tracking_link_dialog(frm);
    }, __('TrackFlow'));
    
    // Add "View Attribution" button
    if (frm.doc.trackflow_visitor_id) {
        frm.add_custom_button(__('View Attribution'), function() {
            show_lead_attribution(frm);
        }, __('TrackFlow'));
        
        frm.add_custom_button(__('View Journey'), function() {
            show_visitor_journey(frm);
        }, __('TrackFlow'));
    }
    
    // Add "Link to Campaign" button if not already linked
    if (!frm.doc.trackflow_campaign) {
        frm.add_custom_button(__('Link to Campaign'), function() {
            link_to_campaign_dialog(frm);
        }, __('TrackFlow'));
    }
}

function create_tracking_link_dialog(frm) {
    let dialog = new frappe.ui.Dialog({
        title: __('Create Tracking Link'),
        fields: [
            {
                label: __('Title'),
                fieldname: 'title',
                fieldtype: 'Data',
                reqd: 1,
                default: `Lead: ${frm.doc.lead_name || frm.doc.email}`
            },
            {
                label: __('Destination URL'),
                fieldname: 'destination_url',
                fieldtype: 'Data',
                reqd: 1,
                default: frappe.boot.sitename
            },
            {
                label: __('Campaign'),
                fieldname: 'campaign',
                fieldtype: 'Link',
                options: 'Link Campaign'
            },
            {
                label: __('UTM Parameters'),
                fieldname: 'utm_section',
                fieldtype: 'Section Break'
            },
            {
                label: __('Source'),
                fieldname: 'utm_source',
                fieldtype: 'Data',
                default: 'email'
            },
            {
                label: __('Medium'),
                fieldname: 'utm_medium',
                fieldtype: 'Data',
                default: 'lead-nurture'
            },
            {
                label: __('Campaign Name'),
                fieldname: 'utm_campaign',
                fieldtype: 'Data'
            }
        ],
        primary_action_label: __('Create'),
        primary_action: function(values) {
            frappe.call({
                method: 'trackflow.api.tracking.create_tracking_link',
                args: {
                    title: values.title,
                    destination_url: values.destination_url,
                    campaign: values.campaign,
                    utm_source: values.utm_source,
                    utm_medium: values.utm_medium,
                    utm_campaign: values.utm_campaign,
                    lead: frm.doc.name
                },
                callback: function(r) {
                    if (r.message) {
                        dialog.hide();
                        frappe.msgprint({
                            title: __('Tracking Link Created'),
                            message: __('Short URL: {0}', [
                                `<a href="${r.message.short_url}" target="_blank">${r.message.short_url}</a>`
                            ]),
                            indicator: 'green'
                        });
                    }
                }
            });
        }
    });
    dialog.show();
}

function link_to_campaign_dialog(frm) {
    frappe.prompt({
        label: __('Campaign'),
        fieldname: 'campaign',
        fieldtype: 'Link',
        options: 'Link Campaign',
        reqd: 1
    }, function(values) {
        frappe.call({
            method: 'frappe.client.set_value',
            args: {
                doctype: 'CRM Lead',
                name: frm.doc.name,
                fieldname: {
                    'trackflow_campaign': values.campaign
                }
            },
            callback: function() {
                frm.reload_doc();
                frappe.show_alert({
                    message: __('Lead linked to campaign'),
                    indicator: 'green'
                });
            }
        });
    }, __('Link to Campaign'), __('Link'));
}

function show_tracking_summary(frm) {
    // Create HTML for tracking summary
    let html = `
        <div class="trackflow-summary">
            <div class="row">
                <div class="col-md-4">
                    <strong>${__('Source')}</strong><br>
                    ${frm.doc.trackflow_source || 'Direct'}
                </div>
                <div class="col-md-4">
                    <strong>${__('Medium')}</strong><br>
                    ${frm.doc.trackflow_medium || 'None'}
                </div>
                <div class="col-md-4">
                    <strong>${__('Campaign')}</strong><br>
                    ${frm.doc.trackflow_campaign || 'None'}
                </div>
            </div>`;
    
    if (frm.doc.trackflow_first_touch_date) {
        html += `
            <hr>
            <div class="row">
                <div class="col-md-6">
                    <strong>${__('First Touch')}</strong><br>
                    ${frappe.datetime.str_to_user(frm.doc.trackflow_first_touch_date)}
                </div>
                <div class="col-md-6">
                    <strong>${__('Touch Count')}</strong><br>
                    ${frm.doc.trackflow_touch_count || 0}
                </div>
            </div>`;
    }
    
    html += '</div>';
    
    // Add to form
    if (!frm.fields_dict.trackflow_summary_html) {
        frm.set_df_property('trackflow_visitor_id', 'description', html);
    }
}

function show_lead_attribution(frm) {
    frappe.call({
        method: 'trackflow.integrations.crm_lead.get_lead_attribution_data',
        args: {
            lead_name: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                show_attribution_dialog(r.message);
            }
        }
    });
}

function show_visitor_journey(frm) {
    frappe.call({
        method: 'trackflow.integrations.crm_lead.get_visitor_journey',
        args: {
            visitor_id: frm.doc.trackflow_visitor_id
        },
        callback: function(r) {
            if (r.message) {
                show_journey_dialog(r.message);
            }
        }
    });
}

function show_attribution_dialog(data) {
    let dialog = new frappe.ui.Dialog({
        title: __('Lead Attribution Analysis'),
        size: 'large',
        fields: [{
            fieldtype: 'HTML',
            fieldname: 'attribution_html'
        }]
    });
    
    let html = build_attribution_html(data);
    dialog.fields_dict.attribution_html.$wrapper.html(html);
    dialog.show();
}

function show_journey_dialog(data) {
    let dialog = new frappe.ui.Dialog({
        title: __('Visitor Journey'),
        size: 'extra-large',
        fields: [{
            fieldtype: 'HTML',
            fieldname: 'journey_html'
        }]
    });
    
    let html = build_journey_timeline_html(data);
    dialog.fields_dict.journey_html.$wrapper.html(html);
    dialog.show();
}

function build_attribution_html(data) {
    // Build comprehensive attribution analysis HTML
    let html = `<div class="attribution-analysis">`;
    
    // Summary section
    html += `
        <h4>${__('Attribution Summary')}</h4>
        <div class="row">
            <div class="col-md-6">
                <p><strong>${__('Total Touchpoints')}:</strong> ${data.touchpoint_count || 0}</p>
                <p><strong>${__('Journey Duration')}:</strong> ${data.journey_duration || 'N/A'}</p>
            </div>
            <div class="col-md-6">
                <p><strong>${__('Conversion Probability')}:</strong> ${data.conversion_probability || 'N/A'}</p>
                <p><strong>${__('Engagement Score')}:</strong> ${data.engagement_score || 0}</p>
            </div>
        </div>`;
    
    // Channel breakdown
    if (data.channel_breakdown) {
        html += `
            <hr>
            <h4>${__('Channel Contribution')}</h4>
            <div class="channel-breakdown">`;
        
        for (let channel of data.channel_breakdown) {
            html += `
                <div class="channel-item">
                    <strong>${channel.name}</strong>: ${channel.touches} touches (${channel.percentage}%)
                </div>`;
        }
        html += `</div>`;
    }
    
    html += `</div>`;
    return html;
}

function build_journey_timeline_html(data) {
    let html = `<div class="visitor-journey-timeline">`;
    
    if (!data.events || data.events.length === 0) {
        html += `<p>${__('No journey data available')}</p>`;
    } else {
        html += `<div class="timeline">`;
        
        for (let event of data.events) {
            html += `
                <div class="timeline-item">
                    <div class="timeline-badge">
                        <i class="fa fa-${get_event_icon(event.type)}"></i>
                    </div>
                    <div class="timeline-content">
                        <h5>${event.title}</h5>
                        <p>${event.description}</p>
                        <small class="text-muted">${frappe.datetime.str_to_user(event.timestamp)}</small>
                    </div>
                </div>`;
        }
        
        html += `</div>`;
    }
    
    html += `</div>`;
    return html;
}

function get_event_icon(event_type) {
    const icons = {
        'page_view': 'eye',
        'link_click': 'link',
        'form_submit': 'check',
        'conversion': 'star',
        'email_open': 'envelope-open',
        'email_click': 'envelope'
    };
    return icons[event_type] || 'circle';
}

function set_tracking_from_route(frm) {
    // Set tracking data from route options
    let data = frappe.route_options.trackflow_data;
    if (data) {
        frm.set_value('trackflow_visitor_id', data.visitor_id);
        frm.set_value('trackflow_source', data.source);
        frm.set_value('trackflow_medium', data.medium);
        frm.set_value('trackflow_campaign', data.campaign);
        frm.set_value('trackflow_first_touch_date', data.timestamp);
        frm.set_value('trackflow_touch_count', 1);
    }
}

// Add custom CSS
frappe.ui.form.on('CRM Lead', {
    onload: function() {
        if (!window.trackflow_css_added) {
            $('<style>')
                .prop('type', 'text/css')
                .html(`
                    .trackflow-summary {
                        background: #f5f5f5;
                        padding: 15px;
                        border-radius: 4px;
                        margin: 10px 0;
                    }
                    .timeline {
                        position: relative;
                        padding: 20px 0;
                    }
                    .timeline-item {
                        position: relative;
                        padding-left: 60px;
                        margin-bottom: 20px;
                    }
                    .timeline-badge {
                        position: absolute;
                        left: 0;
                        width: 40px;
                        height: 40px;
                        background: #2563eb;
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: white;
                    }
                    .timeline-content {
                        background: white;
                        padding: 15px;
                        border-radius: 4px;
                        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                    }
                `)
                .appendTo('head');
            window.trackflow_css_added = true;
        }
    }
});
