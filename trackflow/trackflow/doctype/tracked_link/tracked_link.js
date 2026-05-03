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
            frm.add_custom_button(__('Copy Link'), function() {
                frm.events.copy_tracking_link(frm);
            }).addClass('btn-primary');

            frm.add_custom_button(__('View Analytics'), function() {
                frappe.set_route('query-report', 'Link Analytics', {
                    tracked_link: frm.doc.name
                });
            });
        }
    },

    campaign: function(frm) {
        if (frm.doc.campaign) {
            frappe.db.get_value('Link Campaign', frm.doc.campaign, ['source', 'medium'], function(r) {
                if (r) {
                    if (r.source && !frm.doc.source) {
                        frm.set_value('source', r.source);
                    }
                    if (r.medium && !frm.doc.medium) {
                        frm.set_value('medium', r.medium);
                    }
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

    get_tracking_url: function(frm) {
        const base_url = window.location.origin;
        return `${base_url}/r/${frm.doc.short_code}`;
    }
});
