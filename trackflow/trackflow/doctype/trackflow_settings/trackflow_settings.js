// Copyright (c) 2024, TrackFlow and contributors
// For license information, please see license.txt

frappe.ui.form.on('TrackFlow Settings', {
	refresh: function(frm) {
		// Add custom buttons
		if (!frm.is_new()) {
			frm.add_custom_button(__('Generate API Key'), function() {
				frappe.call({
					method: 'trackflow.trackflow.doctype.trackflow_settings.trackflow_settings.generate_api_key',
					callback: function(r) {
						if (r.message) {
							frappe.msgprint({
								title: __('New API Key Generated'),
								message: __('API Key: {0}<br><br>Please copy and save this key securely. It will not be shown again.', [r.message]),
								indicator: 'green'
							});
						}
					}
				});
			});

			frm.add_custom_button(__('Test Email Notification'), function() {
				frappe.call({
					method: 'trackflow.trackflow.doctype.trackflow_settings.trackflow_settings.test_email_notification',
					callback: function(r) {
						if (r.message) {
							frappe.msgprint(__('Test email sent successfully!'));
						}
					}
				});
			});
		}
	},

	validate: function(frm) {
		// Validate settings using actual field names
		if (frm.doc.cookie_expires_days && frm.doc.cookie_expires_days < 1) {
			frappe.throw(__('Cookie expiration must be at least 1 day'));
		}

		if (frm.doc.attribution_window_days && frm.doc.attribution_window_days < 1) {
			frappe.throw(__('Attribution window must be at least 1 day'));
		}

		if (frm.doc.short_code_length && frm.doc.short_code_length < 3) {
			frappe.throw(__('Short code length must be at least 3 characters'));
		}
	}
});
