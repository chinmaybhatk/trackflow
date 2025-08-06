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
        # Fix: TrackFlow Settings is not a Single DocType, so we need to get the document differently
        try:
            settings = frappe.get_doc("TrackFlow Settings", "TrackFlow Settings")
            if not settings.enable_tracking:
                return response
        except:
            # If settings don't exist or can't be accessed, skip tracking
            return response
            
        # For now, skip tracking until Visitor DocType is created
        # TODO: Implement tracking once proper DocTypes are in place
        # track_page_view()
        
    except Exception as e:
        # Don't break the response for tracking errors
        frappe.log_error(f"TrackFlow tracking error: {str(e)}")
        
    return response


def track_page_view():
    """Track a page view"""
    # Temporarily disabled until Visitor DocType exists
    pass
    # Original implementation commented out:
    # from trackflow.utils import get_visitor_from_request, create_visitor_session
    # 
    # # Get or create visitor
    # visitor = get_visitor_from_request()
    # if not visitor:
    #     return
    #     
    # # Update last seen
    # visitor.last_seen = frappe.utils.now()
    # visitor.page_views = (visitor.page_views or 0) + 1
    # visitor.save(ignore_permissions=True)
    # 
    # # Create or update session
    # session_id = frappe.request.cookies.get('trackflow_session')
    # if session_id:
    #     # Try to get existing session
    #     if frappe.db.exists("Visitor Session", {"session_id": session_id}):
    #         session = frappe.get_doc("Visitor Session", {"session_id": session_id})
    #         session.page_views = (session.page_views or 0) + 1
    #         session.last_activity = frappe.utils.now()
    #         session.save(ignore_permissions=True)
    #     else:
    #         # Create new session
    #         session = create_visitor_session(visitor, frappe.request.url)
    # else:
    #     # Create new session
    #     session = create_visitor_session(visitor, frappe.request.url)
    #     if session:
    #         # Set session cookie
    #         frappe.local.cookie_manager.set_cookie('trackflow_session', session.session_id)
    # 
    # # Record page view event
    # if session:
    #     record_page_view_event(visitor, session, frappe.request.url)


def record_page_view_event(visitor, session, url):
    """Record a page view event"""
    # Temporarily disabled until Visitor Event DocType exists
    pass
    # try:
    #     event = frappe.new_doc("Visitor Event")
    #     event.visitor = visitor.name
    #     event.session = session.name if session else None
    #     event.event_type = "page_view"
    #     event.event_category = "navigation"
    #     event.url = url
    #     event.timestamp = frappe.utils.now()
    #     event.insert(ignore_permissions=True)
    # except Exception as e:
    #     frappe.log_error(f"Error recording page view: {str(e)}")


def track_event(visitor_id, event_type, event_data=None):
    """Track a custom event"""
    # For now, just log the event since Visitor DocType doesn't exist
    frappe.log_error(f"TrackFlow: Would track event {event_type} for visitor {visitor_id}")
    return None
    
    # Original implementation commented out:
    # try:
    #     if not frappe.db.exists("Visitor", visitor_id):
    #         frappe.log_error(f"Visitor {visitor_id} not found")
    #         return None
    #         
    #     event = frappe.new_doc("Visitor Event")
    #     event.visitor = visitor_id
    #     event.event_type = event_type
    #     event.event_category = event_data.get("category", "custom") if event_data else "custom"
    #     event.event_action = event_data.get("action") if event_data else None
    #     event.event_label = event_data.get("label") if event_data else None
    #     event.event_value = event_data.get("value") if event_data else None
    #     event.url = event_data.get("url", frappe.request.url if frappe.request else None) if event_data else None
    #     event.timestamp = frappe.utils.now()
    #     
    #     # Store additional data as JSON
    #     if event_data:
    #         event.event_data = frappe.as_json(event_data)
    #         
    #     event.insert(ignore_permissions=True)
    #     return event
    #     
    # except Exception as e:
    #     frappe.log_error(f"Error tracking event: {str(e)}")
    #     return None


def track_conversion(visitor_id, conversion_type, conversion_value=None, metadata=None):
    """Track a conversion event"""
    # For now, just log the conversion since Conversion DocType doesn't exist
    frappe.log_error(f"TrackFlow: Would track conversion {conversion_type} for visitor {visitor_id}")
    return None
    
    # Original implementation commented out:
    # try:
    #     if not frappe.db.exists("Visitor", visitor_id):
    #         frappe.log_error(f"Visitor {visitor_id} not found")
    #         return None
    #         
    #     # Create conversion record
    #     conversion = frappe.new_doc("Conversion")
    #     conversion.visitor = visitor_id
    #     conversion.conversion_type = conversion_type
    #     conversion.conversion_value = conversion_value
    #     conversion.conversion_date = frappe.utils.now()
    #     
    #     # Add metadata
    #     if metadata:
    #         conversion.source = metadata.get("source")
    #         conversion.medium = metadata.get("medium")
    #         conversion.campaign = metadata.get("campaign")
    #         conversion.metadata = frappe.as_json(metadata)
    #         
    #     conversion.insert(ignore_permissions=True)
    #     
    #     # Also track as an event
    #     track_event(visitor_id, "conversion", {
    #         "category": "conversion",
    #         "action": conversion_type,
    #         "value": conversion_value,
    #         "metadata": metadata
    #     })
    #     
    #     # Update visitor conversion status
    #     visitor = frappe.get_doc("Visitor", visitor_id)
    #     visitor.has_converted = 1
    #     visitor.conversion_count = (visitor.conversion_count or 0) + 1
    #     visitor.last_conversion_date = frappe.utils.now()
    #     visitor.save(ignore_permissions=True)
    #     
    #     return conversion
    #     
    # except Exception as e:
    #     frappe.log_error(f"Error tracking conversion: {str(e)}")
    #     return None
