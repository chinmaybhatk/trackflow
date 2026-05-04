"""
Tracking module for after_request hook
"""

import frappe
from frappe import _


def after_request(response):
    """Process tracking after request"""
    try:
        if frappe.request and frappe.request.path:
            if frappe.request.path.startswith(("/api/", "/files/", "/private/files/", "/assets/")):
                return response

        if frappe.session and frappe.session.user != "Guest":
            return response

        try:
            if frappe.db.exists("TrackFlow Settings", "TrackFlow Settings"):
                settings = frappe.get_cached_doc("TrackFlow Settings", "TrackFlow Settings")
                if not settings.enable_tracking:
                    return response
        except Exception:
            return response

        track_page_view()

    except Exception as e:
        if frappe.local.conf.get("developer_mode"):
            frappe.log_error(f"TrackFlow tracking error: {str(e)}", "TrackFlow After Request")

    return response


def track_page_view():
    """Track a page view"""
    from trackflow.trackflow.utils import get_visitor_from_request

    result = get_visitor_from_request()
    if not result:
        return

    visitor_id, visitor_name = result
    if not visitor_name:
        return

    frappe.db.set_value("Visitor", visitor_name, {
        "last_seen": frappe.utils.now(),
        "page_views": frappe.db.get_value("Visitor", visitor_name, "page_views", 0) + 1,
    }, update_modified=False)

    session_id = frappe.request.cookies.get("trackflow_session") if frappe.request else None
    if session_id and frappe.db.exists("Visitor Session", {"session_id": session_id}):
        vs_name = frappe.db.get_value("Visitor Session", {"session_id": session_id}, "name")
        frappe.db.set_value("Visitor Session", vs_name, {
            "page_views": frappe.db.get_value("Visitor Session", vs_name, "page_views", 0) + 1,
            "last_activity": frappe.utils.now(),
        }, update_modified=False)
    else:
        from trackflow.utils import create_visitor_session
        visitor_doc = frappe.get_doc("Visitor", visitor_name)
        session = create_visitor_session(visitor_doc, frappe.request.url if frappe.request else None)
        if session:
            frappe.local.cookie_manager.set_cookie("trackflow_session", session.session_id)


def track_event(visitor_id, event_type, event_data=None):
    """Track a custom event"""
    try:
        if not frappe.db.exists("Visitor", {"visitor_id": visitor_id}):
            return None

        event = frappe.new_doc("Visitor Event")
        event.visitor = frappe.db.get_value("Visitor", {"visitor_id": visitor_id}, "name")
        event.event_type = event_type
        event.event_category = event_data.get("category", "custom") if event_data else "custom"
        event.url = event_data.get("url") if event_data else None
        event.timestamp = frappe.utils.now()

        if event_data:
            event.event_data = frappe.as_json(event_data)

        event.insert(ignore_permissions=True)
        return event

    except Exception as e:
        frappe.log_error(f"Error tracking event: {str(e)}", "TrackFlow Event")
        return None


def track_conversion(visitor_id, conversion_type, conversion_value=None, metadata=None):
    """Track a conversion event"""
    try:
        if not frappe.db.exists("Visitor", {"visitor_id": visitor_id}):
            return None

        conversion = frappe.new_doc("Link Conversion")
        conversion.visitor_id = visitor_id
        conversion.conversion_type = conversion_type
        conversion.conversion_value = conversion_value
        conversion.conversion_timestamp = frappe.utils.now()

        if metadata:
            if metadata.get("campaign"):
                conversion.campaign = metadata["campaign"]
            conversion.conversion_metadata = frappe.as_json(metadata)

        conversion.insert(ignore_permissions=True)
        return conversion

    except Exception as e:
        frappe.log_error(f"Error tracking conversion: {str(e)}", "TrackFlow Conversion")
        return None
