// Copyright (c) 2024, Chinmay Bhat and contributors
// For license information, please see license.txt

// TrackFlow Dashboard Scripts
frappe.provide('trackflow');

trackflow = {
    init: function() {
        // Initialize TrackFlow features
        this.setup_realtime();
        this.setup_shortcuts();
    },
    
    setup_realtime: function() {
        // Listen for real-time campaign alerts
        frappe.realtime.on('trackflow_campaign_alert', function(data) {
            frappe.show_alert({
                message: data.message,
                indicator: 'orange'
            });
        });
    },
    
    setup_shortcuts: function() {
        // Add keyboard shortcuts
        frappe.ui.keys.add_shortcut({
            shortcut: 'ctrl+shift+t',
            action: () => {
                frappe.set_route('List', 'Tracked Link');
            },
            description: __('Go to Tracked Links')
        });
    },
    
    create_tracked_link: function(opts) {
        // Quick create tracked link
        frappe.prompt([
            {
                label: 'Link Name',
                fieldname: 'link_name',
                fieldtype: 'Data',
                reqd: 1
            },
            {
                label: 'Destination URL',
                fieldname: 'destination_url',
                fieldtype: 'Data',
                reqd: 1
            },
            {
                label: 'Campaign',
                fieldname: 'campaign',
                fieldtype: 'Link',
                options: 'Link Campaign'
            },
            {
                label: 'UTM Source',
                fieldname: 'utm_source',
                fieldtype: 'Data'
            },
            {
                label: 'UTM Medium',
                fieldname: 'utm_medium',
                fieldtype: 'Data'
            }
        ], (values) => {
            frappe.call({
                method: 'frappe.client.insert',
                args: {
                    doc: {
                        doctype: 'Tracked Link',
                        ...values
                    }
                },
                callback: (r) => {
                    if (r.exc) return;
                    
                    frappe.show_alert({
                        message: __('Tracked link created'),
                        indicator: 'green'
                    });
                    
                    // Copy short URL to clipboard
                    let short_url = frappe.utils.get_url() + '/r/' + r.message.short_code;
                    trackflow.copy_to_clipboard(short_url);
                }
            });
        }, __('Create Tracked Link'), __('Create'));
    },
    
    copy_to_clipboard: function(text) {
        // Copy text to clipboard
        if (navigator.clipboard) {
            navigator.clipboard.writeText(text).then(() => {
                frappe.show_alert({
                    message: __('Short URL copied to clipboard'),
                    indicator: 'green'
                });
            });
        } else {
            // Fallback for older browsers
            let temp = $('<input>');
            $('body').append(temp);
            temp.val(text).select();
            document.execCommand('copy');
            temp.remove();
            
            frappe.show_alert({
                message: __('Short URL copied to clipboard'),
                indicator: 'green'
            });
        }
    },
    
    show_analytics: function(campaign) {
        // Show campaign analytics in modal
        frappe.call({
            method: 'trackflow.api.analytics.get_analytics',
            args: {
                campaign: campaign
            },
            callback: (r) => {
                if (r.exc) return;
                
                let dialog = new frappe.ui.Dialog({
                    title: __('Campaign Analytics'),
                    fields: [
                        {
                            fieldtype: 'HTML',
                            fieldname: 'analytics_html'
                        }
                    ]
                });
                
                dialog.fields_dict.analytics_html.$wrapper.html(
                    trackflow.render_analytics(r.message)
                );
                
                dialog.show();
            }
        });
    },
    
    render_analytics: function(data) {
        // Render analytics HTML
        let html = `
            <div class="trackflow-analytics">
                <div class="row">
                    <div class="col-md-3">
                        <div class="trackflow-metric">
                            <div class="trackflow-metric-label">Total Clicks</div>
                            <div class="trackflow-metric-value">${data.summary.total_clicks}</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="trackflow-metric">
                            <div class="trackflow-metric-label">Unique Visitors</div>
                            <div class="trackflow-metric-value">${data.summary.unique_visitors}</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="trackflow-metric">
                            <div class="trackflow-metric-label">Conversions</div>
                            <div class="trackflow-metric-value">${data.summary.total_conversions}</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="trackflow-metric">
                            <div class="trackflow-metric-label">Conversion Rate</div>
                            <div class="trackflow-metric-value">${data.summary.conversion_rate}%</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        return html;
    }
};

// Initialize when DOM is ready
$(document).ready(function() {
    if (frappe.boot && frappe.boot.user) {
        trackflow.init();
    }
});
