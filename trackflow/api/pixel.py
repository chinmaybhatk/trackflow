import frappe
from frappe import _

@frappe.whitelist(allow_guest=True)
def pixel():
    """
    Serve a 1x1 transparent pixel for tracking
    """
    # Track the pixel request
    try:
        visitor_id = frappe.local.request.args.get("v")
        if visitor_id:
            from trackflow.tracking import track_event
            track_event(
                visitor_id=visitor_id,
                event_type="pixel_view",
                event_data={
                    "referer": frappe.local.request.headers.get("Referer"),
                    "user_agent": frappe.local.request.headers.get("User-Agent"),
                    "ip": frappe.local.request.environ.get("REMOTE_ADDR")
                }
            )
    except Exception as e:
        frappe.log_error(f"Pixel tracking error: {str(e)}")
    
    # Return a 1x1 transparent GIF
    pixel_gif = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
    
    frappe.local.response["Content-Type"] = "image/gif"
    frappe.local.response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    frappe.local.response["Pragma"] = "no-cache"
    frappe.local.response["Expires"] = "0"
    frappe.local.response.data = pixel_gif
    
    return
