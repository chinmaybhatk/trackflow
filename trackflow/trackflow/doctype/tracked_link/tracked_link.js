// Copyright (c) 2024, chinmaybhatk and contributors
// For license information, please see license.txt

frappe.ui.form.on('Tracked Link', {
    refresh: function(frm) {
        frm.set_query('campaign', function() {
            return {
                filters: {
                    'status': ['in', ['Active', 'Draft']]
                }
            };
        });

        if (!frm.is_new()) {
            // Add tracking URL display
            frm.add_custom_button(__('Copy Link'), function() {
                frm.events.copy_tracking_link(frm);
            }).addClass('btn-primary');

            frm.add_custom_button(__('Generate QR Code'), function() {
                frm.events.generate_qr_code(frm);
            });

            frm.add_custom_button(__('View Analytics'), function() {
                frappe.set_route('query-report', 'Link Analytics', {
                    tracked_link: frm.doc.name
                });
            });

            // Show link statistics
            frm.events.show_link_stats(frm);
            
            // Display the full tracking URL
            frm.events.display_tracking_url(frm);
        }

        // Set dynamic help text
        frm.fields_dict['custom_identifier'].set_description(
            'Optional: Use for identifying links in reports (e.g., "newsletter-header", "fb-post-1")'
        );
    },

    campaign: function(frm) {
        if (frm.doc.campaign) {
            // Auto-populate target URL from campaign
            frappe.db.get_value('Link Campaign', frm.doc.campaign, 'target_url', function(r) {
                if (r && r.target_url && !frm.doc.target_url) {
                    frm.set_value('target_url', r.target_url);
                }
            });
        }
    },

    copy_tracking_link: function(frm) {
        const tracking_url = frm.events.get_tracking_url(frm);
        
        if (navigator.clipboard) {
            navigator.clipboard.writeText(tracking_url).then(function() {
                frappe.show_alert({
                    message: __('Tracking link copied to clipboard!'),
                    indicator: 'green'
                });
            });
        } else {
            // Fallback for older browsers
            const temp = $('<input>');
            $('body').append(temp);
            temp.val(tracking_url).select();
            document.execCommand('copy');
            temp.remove();
            frappe.show_alert({
                message: __('Tracking link copied to clipboard!'),
                indicator: 'green'
            });
        }
    },

    generate_qr_code: function(frm) {
        const tracking_url = frm.events.get_tracking_url(frm);
        
        frappe.call({
            method: 'trackflow.utils.qr_generator.generate_qr_code',
            args: {
                url: tracking_url,
                size: 300
            },
            callback: function(r) {
                if (r.message) {
                    const d = new frappe.ui.Dialog({
                        title: __('QR Code for {0}', [frm.doc.short_code]),
                        fields: [
                            {
                                fieldtype: 'HTML',
                                fieldname: 'qr_preview',
                                options: '<div class="text-center"><img src="' + r.message + '" /></div>'
                            }
                        ],
                        primary_action_label: __('Download'),
                        primary_action: function() {
                            const link = document.createElement('a');
                            link.download = frm.doc.short_code + '_qr.png';
                            link.href = r.message;
                            link.click();
                            d.hide();
                        }
                    });
                    d.show();
                }
            }
        });
    },

    get_tracking_url: function(frm) {
        const base_url = frappe.boot.trackflow_settings?.redirect_domain || window.location.origin;
        return `${base_url}/redirect/${frm.doc.short_code}`;
    },

    display_tracking_url: function(frm) {
        const tracking_url = frm.events.get_tracking_url(frm);
        
        frm.set_df_property('tracking_url_display', 'options', `
            <div class="alert alert-info">
                <strong>${__('Tracking URL')}:</strong><br>
                <code style="user-select: all;">${tracking_url}</code>
                <button class="btn btn-xs btn-default pull-right" onclick="frappe.utils.copy_to_clipboard('${tracking_url}')">
                    <i class="fa fa-copy"></i> ${__('Copy')}
                </button>
            </div>
        `);
        frm.refresh_field('tracking_url_display');
    },

    show_link_stats: function(frm) {
        frappe.call({
            method: 'trackflow.api.analytics.get_link_stats',
            args: {
                link_id: frm.doc.name
            },
            callback: function(r) {
                if (r.message) {
                    const stats = r.message;
                    frm.dashboard.add_indicator(__('Total Clicks: {0}', [stats.total_clicks]), 'blue');
                    frm.dashboard.add_indicator(__('Unique Clicks: {0}', [stats.unique_clicks]), 'green');
                    frm.dashboard.add_indicator(__('Last Click: {0}', [stats.last_click || 'Never']), 'orange');
                    
                    if (stats.ctr) {
                        frm.dashboard.add_indicator(__('CTR: {0}%', [stats.ctr.toFixed(2)]), 'green');
                    }
                }
            }
        });
    },

    tags: function(frm) {
        // Clean up tags input
        if (frm.doc.tags) {
            const cleaned_tags = frm.doc.tags
                .split(',')
                .map(tag => tag.trim())
                .filter(tag => tag)
                .join(', ');
            
            if (cleaned_tags !== frm.doc.tags) {
                frm.set_value('tags', cleaned_tags);
            }
        }
    }
});
