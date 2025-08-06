"""
Tracking module for after_request hook
"""

import frappe
from frappe import _

def after_request(response):
    """Process tracking after request"""
    try:
        # Skip if it's an API call or static file
        if frappe.request.path.startswith(("/api/", "/files/", "/private/files/", "/assets/")):
            return response
            
        # Skip if user is logged in (internal users)
        if frappe.session.user != "Guest":
            return response
            
        # Check if tracking is enabled
        if not frappe.db.get_single_value("TrackFlow Settings", "enable_tracking"):
            return response
            
        # Track the page view
        track_page_view()
        
    except Exception as e:
        # Don't break the response for tracking errors
        frappe.log_error(f"TrackFlow tracking error: {str(e)}")
        
    return response


def track_page_view():
    """Track a page view"""
    from trackflow.utils import get_visitor_from_request, create_visitor_session
    
    # Get or create visitor
    visitor = get_visitor_from_request()
    if not visitor:
        return
        
    # Update last seen
    visitor.last_seen = frappe.utils.now()
    visitor.page_views = (visitor.page_views or 0) + 1
    visitor.save(ignore_permissions=True)
    
    # Create or update session
    session_id = frappe.request.cookies.get('trackflow_session')
    if session_id:
        # Try to get existing session
        if frappe.db.exists("Visitor Session", {"session_id": session_id}):
            session = frappe.get_doc("Visitor Session", {"session_id": session_id})
            session.page_views = (session.page_views or 0) + 1
            session.last_activity = frappe.utils.now()
            session.save(ignore_permissions=True)
        else:
            # Create new session
            session = create_visitor_session(visitor, frappe.request.url)
    else:
        # Create new session
        session = create_visitor_session(visitor, frappe.request.url)
        if session:
            # Set session cookie
            frappe.local.cookie_manager.set_cookie('trackflow_session', session.session_id)
    
    # Record page view event
    if session:
        record_page_view_event(visitor, session, frappe.request.url)


def record_page_view_event(visitor, session, url):
    """Record a page view event"""
    try:
        event = frappe.new_doc("Visitor Event")
        event.visitor = visitor.name
        event.session = session.name if session else None
        event.event_type = "page_view"
        event.event_category = "navigation"
        event.url = url
        event.timestamp = frappe.utils.now()
        event.insert(ignore_permissions=True)
    except Exception as e:
        frappe.log_error(f"Error recording page view: {str(e)}")
