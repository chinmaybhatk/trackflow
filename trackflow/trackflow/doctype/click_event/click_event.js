// Copyright (c) 2024, chinmaybhatk and contributors
// For license information, please see license.txt

frappe.ui.form.on('Click Event', {
    refresh: function(frm) {
        // Click events are read-only
        frm.disable_form();
        
        // Add map view if location available
        if (frm.doc.latitude && frm.doc.longitude) {
            frm.add_custom_button(__('View on Map'), function() {
                window.open(`https://maps.google.com/?q=${frm.doc.latitude},${frm.doc.longitude}`, '_blank');
            });
        }
        
        // Add visitor journey button
        if (frm.doc.visitor_id) {
            frm.add_custom_button(__('View Visitor Journey'), function() {
                frappe.set_route('query-report', 'Visitor Journey', {
                    visitor_id: frm.doc.visitor_id
                });
            });
        }
        
        // Display parsed user agent info
        if (frm.doc.user_agent) {
            frm.events.display_device_info(frm);
        }
        
        // Show conversion info if applicable
        if (frm.doc.led_to_conversion) {
            frm.dashboard.add_indicator(__('Led to Conversion'), 'green');
        }
    },
    
    display_device_info: function(frm) {
        let device_info = `
            <div class="frappe-card">
                <div class="card-body">
                    <h5>${__('Device Information')}</h5>
                    <table class="table table-sm">
                        <tr><td><strong>${__('Device')}</strong></td><td>${frm.doc.device_type || 'Unknown'}</td></tr>
                        <tr><td><strong>${__('Browser')}</strong></td><td>${frm.doc.browser || 'Unknown'}</td></tr>
                        <tr><td><strong>${__('OS')}</strong></td><td>${frm.doc.os || 'Unknown'}</td></tr>
                    </table>
                </div>
            </div>
        `;
        
        frm.set_df_property('device_info_html', 'options', device_info);
        frm.refresh_field('device_info_html');
    }
});
