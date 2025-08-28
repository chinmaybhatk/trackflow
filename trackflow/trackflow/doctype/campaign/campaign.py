# Copyright (c) 2024, Chinmay Bhat and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import nowdate, getdate

class Campaign(Document):
    def validate(self):
        self.validate_dates()
        
    def validate_dates(self):
        if self.end_date and getdate(self.end_date) < getdate(self.start_date):
            frappe.throw("End Date cannot be before Start Date")
            
    def on_update(self):
        # Auto-activate campaign if start date reached
        if self.status == "Draft" and getdate(self.start_date) <= getdate(nowdate()):
            self.status = "Active"
            self.save()
            
    def update_metrics(self):
        """Update campaign metrics from tracking data"""
        # Count conversions
        self.actual_conversions = frappe.db.count("Link Conversion", {"campaign": self.name})
        
        # Calculate revenue
        self.actual_revenue = frappe.db.sql("""
            SELECT COALESCE(SUM(conversion_value), 0) 
            FROM `tabLink Conversion` 
            WHERE campaign = %s
        """, self.name)[0][0] or 0
        
        self.save()
        
    @frappe.whitelist()
    def generate_tracking_link(self, target_url):
        """Generate a tracked link for this campaign"""
        from trackflow.api.tracking import create_tracked_link
        
        return create_tracked_link(
            target_url=target_url,
            campaign=self.name,
            source=self.utm_source,
            medium=self.utm_medium,
            term=self.utm_term,
            content=self.utm_content
        )
