import frappe
from frappe import _

def get_context(context):
    """Get context for TrackFlow public dashboard."""
    # Check if user has permission
    if not frappe.has_permission("Campaign", "read"):
        frappe.throw(_("You don't have permission to access this page"), frappe.PermissionError)
    
    context.title = "TrackFlow Analytics Dashboard"
    context.no_cache = 1
    
    # This would typically load a Vue/React app or redirect to the internal dashboard
    # For now, redirect to the internal dashboard page
    frappe.local.response.location = "/app/trackflow-dashboard"
    raise frappe.Redirect