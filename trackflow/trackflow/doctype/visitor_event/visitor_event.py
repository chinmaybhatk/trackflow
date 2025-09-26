import frappe
from frappe.model.document import Document


class VisitorEvent(Document):
    def before_insert(self):
        if not self.timestamp:
            self.timestamp = frappe.utils.now()
    
    def validate(self):
        if not self.event_type:
            frappe.throw("Event Type is required")
        
        if not self.visitor:
            frappe.throw("Visitor is required")
    
    def after_insert(self):
        # Update visitor's last activity
        if self.visitor:
            frappe.db.set_value("Visitor", self.visitor, "last_activity", self.timestamp)
        
        # Update session's last activity if session is linked
        if self.session:
            frappe.db.set_value("Visitor Session", self.session, "last_activity", self.timestamp)