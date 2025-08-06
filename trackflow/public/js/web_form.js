frappe.ui.form.on('Web Form', {
    refresh: function(frm) {
        // Add TrackFlow section to Web Form
        if (!frm.fields_dict.trackflow_section) {
            frm.add_child('fields', {
                fieldname: 'trackflow_section',
                label: 'TrackFlow Settings',
                fieldtype: 'Section Break',
                collapsible: 1
            });
        }
        
        // Show tracking status
        if (frm.doc.trackflow_tracking_enabled) {
            frm.dashboard.add_indicator(__('TrackFlow Tracking: Active'), 'green');
        } else {
            frm.dashboard.add_indicator(__('TrackFlow Tracking: Inactive'), 'grey');
        }
        
        // Add tracking preview button
        if (frm.doc.trackflow_tracking_enabled && frm.doc.name) {
            frm.add_custom_button(__('Preview Tracking'), function() {
                frappe.msgprint({
                    title: __('TrackFlow Tracking Preview'),
                    message: __('This form will track the following conversion goal: {0}', 
                        [frm.doc.trackflow_conversion_goal || 'Not Set']),
                    indicator: 'blue'
                });
            });
        }
    },
    
    trackflow_tracking_enabled: function(frm) {
        // Toggle conversion goal field visibility
        frm.toggle_reqd('trackflow_conversion_goal', frm.doc.trackflow_tracking_enabled);
        frm.toggle_display('trackflow_conversion_goal', frm.doc.trackflow_tracking_enabled);
        
        if (frm.doc.trackflow_tracking_enabled) {
            frappe.msgprint({
                title: __('TrackFlow Tracking Enabled'),
                message: __('Form submissions will be tracked. Please set a conversion goal.'),
                indicator: 'green'
            });
        }
    },
    
    trackflow_conversion_goal: function(frm) {
        // Validate conversion goal
        if (frm.doc.trackflow_conversion_goal && frm.doc.trackflow_conversion_goal.length > 50) {
            frappe.msgprint(__('Conversion goal should be less than 50 characters'));
            frm.set_value('trackflow_conversion_goal', '');
        }
    }
});
