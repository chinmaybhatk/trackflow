import frappe
from frappe import _

def get_context(context):
    """TrackFlow main page - redirect to campaigns"""
    context.no_cache = 1
    context.show_sidebar = False
    
    # Redirect to campaigns page
    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = "/campaigns"