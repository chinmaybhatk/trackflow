import frappe
import json
from datetime import datetime

def get_context(context):
    """Handle tracking pixel requests."""
    # Get visitor ID from path
    visitor_id = frappe.form_dict.get("visitor_id")
    
    if visitor_id:
        # Record pixel fire event
        try:
            visitor = frappe.db.get_value("Visitor", {"visitor_id": visitor_id}, "name")
            if visitor:
                # Update last seen
                frappe.db.set_value("Visitor", visitor, "last_seen", datetime.now())
                
                # Record event if needed
                event_type = frappe.form_dict.get("event")
                if event_type:
                    record_pixel_event(visitor, event_type)
        except Exception as e:
            frappe.log_error(f"Tracking pixel error: {str(e)}", "TrackFlow Pixel")
    
    # Return 1x1 transparent GIF
    frappe.response.headers["Content-Type"] = "image/gif"
    frappe.response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    frappe.response.headers["Pragma"] = "no-cache"
    frappe.response.headers["Expires"] = "0"
    
    # 1x1 transparent GIF
    context.data = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
    
    return context

def record_pixel_event(visitor, event_type):
    """Record custom pixel event."""
    # This can be extended to record specific events
    # For example: email opens, ad impressions, etc.
    pass