import frappe
from frappe import _
import json

@frappe.whitelist(allow_guest=True)
def track():
    """
    Track events via API
    """
    try:
        # Get tracking data from request
        data = json.loads(frappe.local.request.data) if frappe.local.request.data else {}
        
        # Get visitor ID
        visitor_id = data.get("visitor_id") or frappe.local.request.args.get("v")
        if not visitor_id:
            frappe.throw(_("Visitor ID is required"))
        
        # Get event type
        event_type = data.get("event_type", "page_view")
        
        # Track the event
        from trackflow.tracking import track_event
        track_event(
            visitor_id=visitor_id,
            event_type=event_type,
            event_data=data.get("event_data", {})
        )
        
        # Return success response
        return {
            "success": True,
            "message": "Event tracked successfully"
        }
        
    except Exception as e:
        frappe.log_error(f"Tracking API error: {str(e)}")
        return {
            "success": False,
            "message": str(e)
        }
