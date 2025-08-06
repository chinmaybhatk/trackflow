# Copyright (c) 2025, Chinmay Bhat and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class TrackFlowSettings(Document):
    def validate(self):
        # Validate IP ranges if exclude internal traffic is enabled
        if self.exclude_internal_traffic and not self.internal_ip_ranges:
            frappe.throw("Please specify at least one internal IP range when excluding internal traffic")
        
        # Validate attribution window
        if self.attribution_window_days < 1:
            frappe.throw("Attribution window must be at least 1 day")
        
        # Validate allowed domains for cross-domain tracking
        if self.enable_cross_domain_tracking and not self.allowed_domains:
            frappe.throw("Please specify allowed domains for cross-domain tracking")
    
    def on_update(self):
        # Clear cache when settings are updated
        frappe.clear_cache()
        
        # Update website tracking script if tracking is enabled/disabled
        self.update_website_tracking()
    
    def update_website_tracking(self):
        """Update website tracking script based on settings"""
        website_settings = frappe.get_single("Website Settings")
        
        tracking_script = """<!-- TrackFlow Analytics -->
<script src="/api/method/trackflow.api.tracking.get_tracking_script" async></script>
<!-- End TrackFlow Analytics -->"""
        
        if self.enable_tracking:
            # Add tracking script if not present
            if tracking_script not in (website_settings.head_html or ""):
                website_settings.head_html = (website_settings.head_html or "") + "\n" + tracking_script
                website_settings.save()
        else:
            # Remove tracking script if present
            if website_settings.head_html and tracking_script in website_settings.head_html:
                website_settings.head_html = website_settings.head_html.replace(tracking_script, "")
                website_settings.save()
