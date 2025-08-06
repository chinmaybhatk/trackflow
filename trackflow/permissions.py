"""
TrackFlow permissions module
"""

import frappe
from frappe import _

def has_app_permission(doc=None, ptype=None, user=None):
    """Check if user has permission to access TrackFlow app"""
    if not user:
        user = frappe.session.user
    
    # System Manager always has access
    if "System Manager" in frappe.get_roles(user):
        return True
    
    # Check for TrackFlow specific roles
    trackflow_roles = ["TrackFlow Manager", "TrackFlow User"]
    user_roles = frappe.get_roles(user)
    
    if any(role in user_roles for role in trackflow_roles):
        return True
    
    # Check if user has access to any TrackFlow DocTypes
    trackflow_doctypes = [
        "Campaign",
        "Tracking Link",
        "Visitor",
        "Visitor Event",
        "TrackFlow Settings"
    ]
    
    for doctype in trackflow_doctypes:
        if frappe.has_permission(doctype, user=user):
            return True
    
    return False

def get_permission_query_conditions(user):
    """Return query conditions for TrackFlow DocTypes"""
    if not user:
        user = frappe.session.user
    
    if "System Manager" in frappe.get_roles(user) or "TrackFlow Manager" in frappe.get_roles(user):
        # No restrictions for managers
        return ""
    
    if "TrackFlow User" in frappe.get_roles(user):
        # Users can only see their own data
        return f"(`tabTracking Link`.owner = {frappe.db.escape(user)})"
    
    # No access
    return "1=0"

def has_permission(doc, ptype=None, user=None):
    """Check document level permissions"""
    if not user:
        user = frappe.session.user
    
    # System Manager and TrackFlow Manager have full access
    if "System Manager" in frappe.get_roles(user) or "TrackFlow Manager" in frappe.get_roles(user):
        return True
    
    # TrackFlow Users can access their own documents
    if "TrackFlow User" in frappe.get_roles(user):
        if doc.doctype in ["Tracking Link", "Campaign"]:
            return doc.owner == user
        elif doc.doctype in ["Visitor", "Visitor Event"]:
            # Read-only access to visitor data
            return ptype == "read"
    
    return False
