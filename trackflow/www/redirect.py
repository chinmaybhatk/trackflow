import frappe
from frappe import _

no_cache = 1

def get_context(context):
    """Handle redirect for tracked links"""
    # Get tracking ID from path
    path_parts = frappe.request.path.strip('/').split('/')
    
    if len(path_parts) < 2:
        frappe.throw(_("Invalid tracking link"), frappe.DoesNotExistError)
    
    tracking_id = path_parts[-1]
    
    # Get the tracked link
    tracked_link = frappe.db.get_value(
        "Tracked Link",
        {"short_code": tracking_id, "status": "Active"},
        ["name", "destination_url", "campaign", "medium", "source"],
        as_dict=True
    )
    
    if not tracked_link:
        frappe.throw(_("Link not found or expired"), frappe.DoesNotExistError)
    
    # Track the click
    try:
        track_click_event(tracking_id, tracked_link)
    except:
        pass  # Don't fail redirect if tracking fails
    
    # Redirect to target URL
    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = tracked_link.destination_url

def track_click_event(tracking_id, tracked_link):
    """Track click event"""
    try:
        # Get or create visitor ID
        visitor_id = frappe.request.cookies.get("tf_visitor_id")
        if not visitor_id:
            import uuid
            visitor_id = str(uuid.uuid4())
            frappe.local.cookie_manager.set_cookie("tf_visitor_id", visitor_id, 
                                                  max_age=365*24*60*60, httponly=True)
        
        # Create click event
        click_event = frappe.new_doc("Click Event")
        click_event.tracked_link = tracked_link.name
        click_event.short_code = tracking_id
        click_event.campaign = tracked_link.campaign
        click_event.visitor_id = visitor_id
        click_event.ip_address = frappe.local.request_ip
        click_event.user_agent = frappe.request.headers.get("User-Agent", "")
        click_event.referrer = frappe.request.headers.get("Referer", "")
        click_event.utm_source = tracked_link.source
        click_event.utm_medium = tracked_link.medium
        click_event.click_timestamp = frappe.utils.now()
        
        click_event.insert(ignore_permissions=True)
        
        # Update click count
        frappe.db.sql("""
            UPDATE `tabTracked Link` 
            SET click_count = IFNULL(click_count, 0) + 1,
                modified = modified
            WHERE name = %s
        """, tracked_link.name)
        
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Click Event Tracking Error")
