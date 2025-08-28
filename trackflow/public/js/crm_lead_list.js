frappe.listview_settings['CRM Lead'] = frappe.listview_settings['CRM Lead'] || {};

// Extend existing settings
const existing_settings = frappe.listview_settings['CRM Lead'];

frappe.listview_settings['CRM Lead'] = {
    ...existing_settings,
    
    onload: function(listview) {
        // Add TrackFlow buttons to list view
        listview.page.add_action_item(__('Create Campaign'), function() {
            create_campaign_dialog(listview);
        });
        
        listview.page.add_action_item(__('Bulk Create Tracking Links'), function() {
            bulk_create_tracking_links(listview);
        });
        
        // Add custom indicator for tracked leads
        if (!listview.trackflow_indicators_added) {
            add_trackflow_indicators(listview);
            listview.trackflow_indicators_added = true;
        }
    },
    
    get_indicator: function(doc) {
        // Keep existing indicators if any
        if (existing_settings.get_indicator) {
            const indicator = existing_settings.get_indicator(doc);
            if (indicator) return indicator;
        }
        
        // Add TrackFlow specific indicators
        if (doc.trackflow_campaign) {
            return [__('Tracked'), 'blue', 'trackflow_campaign,is,set'];
        }
        return null;
    }
};

function create_campaign_dialog(listview) {
    let dialog = new frappe.ui.Dialog({
        title: __('Create Marketing Campaign'),
        fields: [
            {
                label: __('Campaign Name'),
                fieldname: 'campaign_name',
                fieldtype: 'Data',
                reqd: 1
            },
            {
                label: __('Campaign Type'),
                fieldname: 'campaign_type',
                fieldtype: 'Select',
                options: 'Email Marketing\nSocial Media\nContent Marketing\nSearch Marketing\nEvent',
                reqd: 1
            },
            {
                label: __('Budget'),
                fieldname: 'budget',
                fieldtype: 'Currency'
            },
            {
                label: __('Start Date'),
                fieldname: 'start_date',
                fieldtype: 'Date',
                default: frappe.datetime.get_today()
            },
            {
                label: __('End Date'),
                fieldname: 'end_date',
                fieldtype: 'Date'
            }
        ],
        primary_action_label: __('Create'),
        primary_action: function(values) {
            frappe.call({
                method: 'trackflow.api.campaign.create_campaign',
                args: values,
                callback: function(r) {
                    if (r.message) {
                        dialog.hide();
                        frappe.show_alert({
                            message: __('Campaign created successfully'),
                            indicator: 'green'
                        });
                        
                        // Ask if user wants to link selected leads
                        if (listview.get_checked_items().length > 0) {
                            link_leads_to_campaign(listview, r.message.name);
                        }
                    }
                }
            });
        }
    });
    dialog.show();
}

function bulk_create_tracking_links(listview) {
    const checked_items = listview.get_checked_items();
    
    if (checked_items.length === 0) {
        frappe.msgprint(__('Please select leads to create tracking links'));
        return;
    }
    
    let dialog = new frappe.ui.Dialog({
        title: __('Bulk Create Tracking Links'),
        fields: [
            {
                label: __('Base URL'),
                fieldname: 'base_url',
                fieldtype: 'Data',
                reqd: 1,
                default: frappe.boot.sitename
            },
            {
                label: __('Campaign'),
                fieldname: 'campaign',
                fieldtype: 'Link',
                options: 'Link Campaign',
                reqd: 1
            },
            {
                label: __('UTM Source'),
                fieldname: 'utm_source',
                fieldtype: 'Data',
                default: 'email'
            },
            {
                label: __('UTM Medium'),
                fieldname: 'utm_medium',
                fieldtype: 'Data',
                default: 'bulk-email'
            }
        ],
        primary_action_label: __('Create Links'),
        primary_action: function(values) {
            frappe.call({
                method: 'trackflow.api.tracking.bulk_create_tracking_links',
                args: {
                    leads: checked_items.map(item => item.name),
                    base_url: values.base_url,
                    campaign: values.campaign,
                    utm_source: values.utm_source,
                    utm_medium: values.utm_medium
                },
                callback: function(r) {
                    if (r.message) {
                        dialog.hide();
                        frappe.msgprint(__('Created {0} tracking links', [r.message.length]));
                        listview.refresh();
                    }
                }
            });
        }
    });
    dialog.show();
}

function link_leads_to_campaign(listview, campaign) {
    frappe.confirm(
        __('Link selected leads to the campaign?'),
        function() {
            const leads = listview.get_checked_items().map(item => item.name);
            
            frappe.call({
                method: 'trackflow.api.campaign.link_leads_to_campaign',
                args: {
                    campaign: campaign,
                    leads: leads
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.show_alert({
                            message: __('Linked {0} leads to campaign', [r.message.count]),
                            indicator: 'green'
                        });
                        listview.refresh();
                    }
                }
            });
        }
    );
}

function add_trackflow_indicators(listview) {
    // Add visual indicators for tracked leads in list view
    listview.$result.on('render-complete', function() {
        listview.$result.find('.list-row').each(function() {
            const data = $(this).data();
            if (data && data.trackflow_campaign) {
                // Add a small tracking icon
                if (!$(this).find('.trackflow-indicator').length) {
                    $(this).find('.list-subject').append(
                        '<span class="trackflow-indicator" title="' + __('Tracked Lead') + '">' +
                        '<i class="fa fa-link text-primary"></i></span>'
                    );
                }
            }
        });
    });
}

// Add custom CSS for indicators
if (!window.trackflow_list_css_added) {
    $('<style>')
        .prop('type', 'text/css')
        .html(`
            .trackflow-indicator {
                margin-left: 8px;
                font-size: 12px;
            }
            .trackflow-indicator i {
                opacity: 0.7;
            }
        `)
        .appendTo('head');
    window.trackflow_list_css_added = true;
}
