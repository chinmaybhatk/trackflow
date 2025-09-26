# Copyright (c) 2025, Chinmay Bhat and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

def get_settings():
    """Get or create TrackFlow Settings singleton"""
    try:
        return frappe.get_single("TrackFlow Settings")
    except frappe.DoesNotExistError:
        # Create default settings if it doesn't exist
        settings = frappe.new_doc("TrackFlow Settings")
        settings.insert(ignore_permissions=True)
        return settings

class TrackFlowSettings(Document):
    def validate(self):
        # Validate IP ranges if exclude internal traffic is enabled
        if getattr(self, 'exclude_internal_traffic', 0) and not getattr(self, 'internal_ip_ranges', []):
            frappe.throw("Please specify at least one internal IP range when excluding internal traffic")
        
        # Validate attribution window
        attribution_window = getattr(self, 'attribution_window_days', 30)
        if attribution_window and attribution_window < 1:
            frappe.throw("Attribution window must be at least 1 day")
    
    def on_update(self):
        # Clear cache when settings are updated
        frappe.clear_cache()
        
        # Update website tracking script if tracking is enabled/disabled
        self.update_website_tracking()
    
    def update_website_tracking(self):
        """Update website tracking script based on settings"""
        try:
            website_settings = frappe.get_single("Website Settings")
            
            tracking_script = """<!-- TrackFlow Analytics -->
<script src="/api/method/trackflow.api.tracking.get_tracking_script" async></script>
<!-- End TrackFlow Analytics -->"""
            
            enable_tracking = getattr(self, 'enable_tracking', 0)
            if enable_tracking:
                # Add tracking script if not present
                if tracking_script not in (website_settings.head_html or ""):
                    website_settings.head_html = (website_settings.head_html or "") + "\n" + tracking_script
                    website_settings.save()
            else:
                # Remove tracking script if present
                if website_settings.head_html and tracking_script in website_settings.head_html:
                    website_settings.head_html = website_settings.head_html.replace(tracking_script, "")
                    website_settings.save()
        except Exception as e:
            # Log error but don't break the settings save
            frappe.log_error(f"Error updating website tracking: {str(e)}", "TrackFlow Settings")

@frappe.whitelist()
def generate_api_key():
    """Generate a new API key for TrackFlow"""
    import secrets
    api_key = secrets.token_urlsafe(32)
    
    # Create or update API key document
    try:
        api_key_doc = frappe.get_doc("TrackFlow API Key", {"user": frappe.session.user})
        api_key_doc.api_key = api_key
        api_key_doc.save()
    except frappe.DoesNotExistError:
        api_key_doc = frappe.new_doc("TrackFlow API Key")
        api_key_doc.user = frappe.session.user
        api_key_doc.api_key = api_key
        api_key_doc.insert()
    
    return api_key

@frappe.whitelist()
def test_email_notification():
    """Send a test email notification"""
    try:
        frappe.sendmail(
            recipients=[frappe.session.user],
            subject="TrackFlow Test Notification",
            message="This is a test email from TrackFlow. Email notifications are working correctly."
        )
        return True
    except Exception as e:
        frappe.log_error(f"Failed to send test email: {str(e)}")
        frappe.throw("Failed to send test email. Please check your email configuration.")

@frappe.whitelist()
def clear_click_queue():
    """Clear pending click events from the queue"""
    # This would typically clear a Redis queue or similar
    # For now, just return a placeholder
    return 0
