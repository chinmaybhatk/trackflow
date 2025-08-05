// Copyright (c) 2024, chinmaybhatk and contributors
// For license information, please see license.txt

frappe.ui.form.on('Link Template', {
    refresh: function(frm) {
        // Add preview button
        if (!frm.is_new()) {
            frm.add_custom_button(__('Preview Template'), function() {
                frm.events.preview_template(frm);
            });
            
            frm.add_custom_button(__('Create Campaign'), function() {
                frm.events.create_campaign_from_template(frm);
            }).addClass('btn-primary');
        }
        
        // Add template variables help
        frm.set_df_property('template_variables', 'description', 
            'Available variables: {campaign_name}, {date}, {user}, {custom_1}, {custom_2}, etc.'
        );
    },
    
    preview_template: function(frm) {
        const sample_data = {
            campaign_name: 'Sample Campaign',
            date: frappe.datetime.nowdate(),
            user: frappe.session.user_fullname,
            custom_1: 'Value 1',
            custom_2: 'Value 2'
        };
        
        const preview_url = frm.events.apply_template(frm, frm.doc.url_template, sample_data);
        
        frappe.msgprint({
            title: __('Template Preview'),
            message: `
                <p><strong>Template URL:</strong><br>
                <code>${frm.doc.url_template}</code></p>
                <p><strong>Preview Result:</strong><br>
                <code>${preview_url}</code></p>
                <p><small>This is a preview with sample data</small></p>
            `,
            indicator: 'blue'
        });
    },
    
    apply_template: function(frm, template, data) {
        let result = template;
        for (let key in data) {
            result = result.replace(new RegExp(`{${key}}`, 'g'), data[key]);
        }
        return result;
    },
    
    create_campaign_from_template: function(frm) {
        frappe.prompt([
            {
                fieldname: 'campaign_name',
                label: 'Campaign Name',
                fieldtype: 'Data',
                reqd: 1
            },
            {
                fieldname: 'campaign_type',
                label: 'Campaign Type',
                fieldtype: 'Select',
                options: 'Email\nSocial Media\nSearch\nDisplay\nAffiliate\nOther',
                default: frm.doc.default_campaign_type
            },
            {
                fieldname: 'start_date',
                label: 'Start Date',
                fieldtype: 'Date',
                default: frappe.datetime.nowdate(),
                reqd: 1
            },
            {
                fieldname: 'end_date',
                label: 'End Date',
                fieldtype: 'Date'
            }
        ], function(values) {
            frappe.call({
                method: 'trackflow.trackflow.doctype.link_template.link_template.create_campaign_from_template',
                args: {
                    template: frm.doc.name,
                    campaign_data: values
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.show_alert({
                            message: __('Campaign created successfully'),
                            indicator: 'green'
                        });
                        frappe.set_route('Form', 'Link Campaign', r.message);
                    }
                }
            });
        }, __('Create Campaign from Template'), __('Create'));
    }
});
