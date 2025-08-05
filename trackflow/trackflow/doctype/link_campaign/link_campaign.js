// Copyright (c) 2024, chinmaybhatk and contributors
// For license information, please see license.txt

frappe.ui.form.on('Link Campaign', {
    refresh: function(frm) {
        frm.set_query('template', function() {
            return {
                filters: {
                    'is_active': 1
                }
            };
        });

        // Add campaign metrics display
        if (!frm.is_new()) {
            frm.add_custom_button(__('View Analytics'), function() {
                frappe.set_route('query-report', 'Link Campaign Analytics', {
                    campaign: frm.doc.name
                });
            });

            frm.add_custom_button(__('Generate Links'), function() {
                frm.events.generate_links(frm);
            });

            frm.add_custom_button(__('Duplicate Campaign'), function() {
                frm.events.duplicate_campaign(frm);
            });

            // Add live statistics
            frm.events.show_campaign_stats(frm);
        }

        // Set dynamic UTM defaults
        if (frm.is_new()) {
            frm.set_value('utm_source', 'trackflow');
            frm.set_value('utm_medium', frm.doc.campaign_type || 'email');
        }

        // Add help text
        frm.fields_dict['target_url'].set_description(
            'The destination URL where users will be redirected. Must include http:// or https://'
        );
    },

    campaign_type: function(frm) {
        // Auto-set UTM medium based on campaign type
        const utm_mappings = {
            'Email': 'email',
            'Social Media': 'social',
            'Search': 'cpc',
            'Display': 'display',
            'Affiliate': 'affiliate',
            'Other': 'other'
        };
        
        if (utm_mappings[frm.doc.campaign_type]) {
            frm.set_value('utm_medium', utm_mappings[frm.doc.campaign_type]);
        }
    },

    target_url: function(frm) {
        // Validate URL format
        if (frm.doc.target_url && !frm.doc.target_url.match(/^https?:\/\//)) {
            frappe.msgprint(__('Target URL must start with http:// or https://'));
            frm.set_value('target_url', '');
        }
    },

    generate_links: function(frm) {
        frappe.prompt([
            {
                fieldname: 'count',
                label: __('Number of Links'),
                fieldtype: 'Int',
                default: 10,
                reqd: 1
            },
            {
                fieldname: 'custom_identifiers',
                label: __('Custom Identifiers (comma-separated)'),
                fieldtype: 'Small Text',
                description: 'Leave blank to auto-generate'
            },
            {
                fieldname: 'link_tags',
                label: __('Tags (comma-separated)'),
                fieldtype: 'Small Text'
            }
        ], function(values) {
            frappe.call({
                method: 'trackflow.api.links.bulk_generate_links',
                args: {
                    campaign: frm.doc.name,
                    count: values.count,
                    custom_identifiers: values.custom_identifiers,
                    tags: values.link_tags
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.msgprint({
                            title: __('Links Generated'),
                            message: __('Successfully generated {0} tracking links', [r.message.count]),
                            indicator: 'green'
                        });
                        frm.reload_doc();
                    }
                }
            });
        }, __('Generate Campaign Links'), __('Generate'));
    },

    duplicate_campaign: function(frm) {
        frappe.prompt([
            {
                fieldname: 'new_name',
                label: __('New Campaign Name'),
                fieldtype: 'Data',
                default: frm.doc.campaign_name + ' (Copy)',
                reqd: 1
            },
            {
                fieldname: 'copy_links',
                label: __('Copy Existing Links'),
                fieldtype: 'Check',
                default: 0
            }
        ], function(values) {
            frappe.call({
                method: 'trackflow.api.campaign.duplicate_campaign',
                args: {
                    source_campaign: frm.doc.name,
                    new_name: values.new_name,
                    copy_links: values.copy_links
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.msgprint(__('Campaign duplicated successfully'));
                        frappe.set_route('Form', 'Link Campaign', r.message);
                    }
                }
            });
        }, __('Duplicate Campaign'), __('Duplicate'));
    },

    show_campaign_stats: function(frm) {
        frappe.call({
            method: 'trackflow.api.analytics.get_campaign_stats',
            args: {
                campaign: frm.doc.name
            },
            callback: function(r) {
                if (r.message) {
                    const stats = r.message;
                    frm.dashboard.add_indicator(__('Total Links: {0}', [stats.total_links]), 'blue');
                    frm.dashboard.add_indicator(__('Total Clicks: {0}', [stats.total_clicks]), 'green');
                    frm.dashboard.add_indicator(__('Unique Visitors: {0}', [stats.unique_visitors]), 'orange');
                    
                    if (stats.conversion_rate) {
                        frm.dashboard.add_indicator(__('Conversion Rate: {0}%', 
                            [stats.conversion_rate.toFixed(2)]), 'green');
                    }
                }
            }
        });
    }
});

// Child table events
frappe.ui.form.on('Campaign Link Variant', {
    weight: function(frm, cdt, cdn) {
        frm.events.validate_weights(frm);
    },

    variant_add: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        row.weight = 100; // Default weight
        frm.refresh_field('variants');
    }
});
