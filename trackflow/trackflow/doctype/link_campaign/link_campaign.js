// Copyright (c) 2024, chinmaybhatk and contributors
// For license information, please see license.txt

frappe.ui.form.on('Link Campaign', {
    refresh: function(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__('View Analytics'), function() {
                frappe.set_route('query-report', 'Link Campaign Analytics', {
                    campaign: frm.doc.name
                });
            });

            frm.add_custom_button(__('Duplicate Campaign'), function() {
                frm.events.duplicate_campaign(frm);
            });
        }

        if (frm.is_new()) {
            frm.set_value('source', 'trackflow');
            frm.set_value('medium', frm.doc.campaign_type || 'email');
        }
    },

    campaign_type: function(frm) {
        const utm_mappings = {
            'Email': 'email',
            'Social Media': 'social',
            'Search': 'cpc',
            'Display': 'display',
            'Affiliate': 'affiliate',
            'Other': 'other'
        };

        if (utm_mappings[frm.doc.campaign_type]) {
            frm.set_value('medium', utm_mappings[frm.doc.campaign_type]);
        }
    },

    duplicate_campaign: function(frm) {
        frappe.prompt([
            {
                fieldname: 'new_name',
                label: __('New Campaign Name'),
                fieldtype: 'Data',
                default: frm.doc.campaign_name + ' (Copy)',
                reqd: 1
            }
        ], function(values) {
            frappe.call({
                method: 'trackflow.api.campaign.duplicate_campaign',
                args: {
                    source_campaign: frm.doc.name,
                    new_name: values.new_name
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.msgprint(__('Campaign duplicated successfully'));
                        frappe.set_route('Form', 'Link Campaign', r.message);
                    }
                }
            });
        }, __('Duplicate Campaign'), __('Duplicate'));
    }
});
