import frappe
from frappe.model.document import Document


class Conversion(Document):
    def before_insert(self):
        if not self.timestamp:
            self.timestamp = frappe.utils.now()
    
    def validate(self):
        if not self.visitor:
            frappe.throw("Visitor is required")
        
        if not self.conversion_type:
            frappe.throw("Conversion Type is required")
    
    def after_insert(self):
        # Update visitor's conversion count
        if self.visitor:
            frappe.db.sql("""
                UPDATE `tabVisitor`
                SET total_conversions = (
                    SELECT COUNT(*)
                    FROM `tabConversion`
                    WHERE visitor = %(visitor)s
                )
                WHERE name = %(visitor)s
            """, {"visitor": self.visitor})
            
        # Update campaign conversion metrics if linked
        if self.campaign:
            self.update_campaign_metrics()
    
    def update_campaign_metrics(self):
        campaign_stats = frappe.get_doc("Link Campaign", self.campaign)
        campaign_stats.update_conversion_metrics()
        campaign_stats.save()