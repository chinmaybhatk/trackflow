import frappe
from frappe import _
import json
from urllib.parse import urlparse, parse_qs

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
        {"short_code": tracking_id, "is_active": 1},
        ["name", "target_url", "campaign", "link_campaign"],
        as_dict=True
    )
    
    if not tracked_link:
        frappe.throw(_("Link not found or expired"), frappe.DoesNotExistError)
    
    # Track the click
    track_click_event(tracked_link, frappe.request)
    
    # Redirect to target URL
    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = tracked_link.target_url
    raise frappe.Redirect

def handle_redirect(tracking_id):
    """API endpoint for handling redirects"""
    try:
        tracked_link = frappe.get_doc("Tracked Link", {"short_code": tracking_id})
        
        if not tracked_link.is_active:
            frappe.throw(_("Link is inactive"))
        
        # Track the click
        track_click_event(tracked_link, frappe.request)
        
        # Update click count
        frappe.db.set_value("Tracked Link", tracked_link.name, "click_count", 
                          tracked_link.click_count + 1, update_modified=False)
        
        frappe.db.commit()
        
        # Redirect
        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = tracked_link.target_url
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "TrackFlow Redirect Error")
        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = "/404"

def track_click_event(tracked_link, request):
    """Track click event with visitor information"""
    try:
        # Get visitor info
        visitor_id = request.cookies.get("tf_visitor_id")
        
        # Create click event
        click_event = frappe.new_doc("Click Event")
        click_event.tracked_link = tracked_link.name
        click_event.campaign = tracked_link.campaign or tracked_link.link_campaign
        click_event.visitor_id = visitor_id
        click_event.ip_address = frappe.local.request_ip
        click_event.user_agent = request.headers.get("User-Agent", "")
        click_event.referrer = request.headers.get("Referer", "")
        
        # Parse UTM parameters if present
        if "?" in tracked_link.target_url:
            parsed = urlparse(tracked_link.target_url)
            params = parse_qs(parsed.query)
            click_event.utm_source = params.get("utm_source", [""])[0]
            click_event.utm_medium = params.get("utm_medium", [""])[0]
            click_event.utm_campaign = params.get("utm_campaign", [""])[0]
            click_event.utm_term = params.get("utm_term", [""])[0]
            click_event.utm_content = params.get("utm_content", [""])[0]
        
        click_event.insert(ignore_permissions=True)
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Click Event Tracking Error")

def before_request():
    """Set visitor cookie before processing request"""
    if not frappe.request.cookies.get("tf_visitor_id"):
        import uuid
        visitor_id = str(uuid.uuid4())
        frappe.local.cookie_manager.set_cookie("tf_visitor_id", visitor_id, 
                                              max_age=365*24*60*60, httponly=True)
