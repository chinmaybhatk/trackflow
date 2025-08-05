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
							frm.reload_doc();
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

			frm.add_custom_button(__('Clear Click Queue'), function() {
				frappe.confirm(
					__('Are you sure you want to clear the click queue? This will delete all pending click events.'),
					function() {
						frappe.call({
							method: 'trackflow.trackflow.doctype.trackflow_settings.trackflow_settings.clear_click_queue',
							callback: function(r) {
								if (r.message) {
									frappe.msgprint(__('Click queue cleared. {0} events deleted.', [r.message]));
								}
							}
						});
					}
				);
			});
		}

		// Show/hide fields based on settings
		frm.toggle_display('notification_recipients', frm.doc.enable_email_notifications);
		frm.toggle_display('click_notification_threshold', frm.doc.enable_email_notifications);
		frm.toggle_display('bot_user_agents', frm.doc.enable_bot_detection);
	},

	enable_email_notifications: function(frm) {
		frm.toggle_display('notification_recipients', frm.doc.enable_email_notifications);
		frm.toggle_display('click_notification_threshold', frm.doc.enable_email_notifications);
	},

	enable_bot_detection: function(frm) {
		frm.toggle_display('bot_user_agents', frm.doc.enable_bot_detection);
	},

	validate: function(frm) {
		// Validate settings
		if (frm.doc.cookie_duration < 1) {
			frappe.throw(__('Cookie duration must be at least 1 day'));
		}

		if (frm.doc.link_expiry_days && frm.doc.link_expiry_days < 1) {
			frappe.throw(__('Link expiry must be at least 1 day'));
		}

		if (frm.doc.default_redirect_delay < 0) {
			frappe.throw(__('Redirect delay cannot be negative'));
		}
	}
});
