// Copyright (c) 2024, chinmaybhatk and contributors
// For license information, please see license.txt

frappe.ui.form.on('Click Event', {
    refresh: function(frm) {
        frm.disable_form();

        if (frm.doc.visitor_id) {
            frm.add_custom_button(__('View Visitor Journey'), function() {
                frappe.set_route('query-report', 'Visitor Journey', {
                    visitor_id: frm.doc.visitor_id
                });
            });
        }
    }
});
