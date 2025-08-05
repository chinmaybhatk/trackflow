import frappe
from frappe import _
import json
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import hashlib
from frappe.utils import get_request_site_address

def handle_redirect(tracking_id):
    """Handle tracking link redirect and record analytics."""
    try:
        # Get tracking link
        tracking_link = frappe.get_doc("Tracking Link", {"tracking_id": tracking_id})
        
        if not tracking_link or tracking_link.status != "Active":
            frappe.local.response.status_code = 404
            return "Link not found"
        
        # Check if link is expired
        if tracking_link.expires_on and tracking_link.expires_on < datetime.now():
            tracking_link.status = "Expired"
            tracking_link.save(ignore_permissions=True)
            frappe.local.response.status_code = 410
            return "Link has expired"
        
        # Get request details
        ip_address = frappe.get_request_header("X-Forwarded-For") or frappe.local.request_ip
        user_agent = frappe.get_request_header("User-Agent")
        referrer = frappe.get_request_header("Referer") or ""
        
        # Generate or retrieve visitor ID
        visitor_id = get_or_create_visitor_id()
        
        # Get or create visitor record
        visitor = get_or_create_visitor(visitor_id, tracking_link)
        
        # Create or update visitor session
        session = create_or_update_session(visitor.name, ip_address, user_agent)
        
        # Record page view
        record_page_view(session.name, tracking_link, referrer)
        
        # Update tracking link stats
        tracking_link.total_clicks = (tracking_link.total_clicks or 0) + 1
        tracking_link.unique_clicks = frappe.db.count("Page View", {
            "tracking_link": tracking_link.name,
            "visitor": ["is", "set"]
        })
        tracking_link.last_accessed = datetime.now()
        tracking_link.last_accessed_ip = ip_address
        tracking_link.save(ignore_permissions=True)
        
        # Handle CRM integration if applicable
        if tracking_link.enable_crm_tracking:
            handle_crm_integration(tracking_link, visitor, session)
        
        # Build destination URL with tracking parameters
        destination_url = build_destination_url(tracking_link, visitor_id)
        
        # Set cookie for visitor tracking
        frappe.local.cookie_manager.set_cookie(
            "trackflow_visitor",
            visitor_id,
            max_age=365 * 24 * 60 * 60,  # 1 year
            httponly=True
        )
        
        # Redirect to destination
        frappe.local.response.location = destination_url
        frappe.local.response.status_code = 302
        
        return ""
        
    except Exception as e:
        frappe.log_error(f"TrackFlow redirect error: {str(e)}", "TrackFlow Redirect")
        frappe.local.response.status_code = 500
        return "An error occurred"

def get_or_create_visitor_id():
    """Get visitor ID from cookie or create new one."""
    visitor_id = frappe.request.cookies.get("trackflow_visitor")
    
    if not visitor_id:
        # Generate new visitor ID
        visitor_id = hashlib.sha256(
            f"{frappe.local.request_ip}{datetime.now()}{frappe.generate_hash()}".encode()
        ).hexdigest()[:32]
    
    return visitor_id

def get_or_create_visitor(visitor_id, tracking_link):
    """Get or create visitor record."""
    visitor = frappe.db.get_value(
        "Visitor",
        {"visitor_id": visitor_id},
        ["name", "first_seen", "last_seen"],
        as_dict=True
    )
    
    if visitor:
        # Update last seen
        frappe.db.set_value("Visitor", visitor.name, "last_seen", datetime.now())
    else:
        # Create new visitor
        visitor_doc = frappe.get_doc({
            "doctype": "Visitor",
            "visitor_id": visitor_id,
            "first_seen": datetime.now(),
            "last_seen": datetime.now(),
            "first_referrer": frappe.get_request_header("Referer") or "",
            "first_landing_page": tracking_link.destination_url,
            "utm_source": tracking_link.utm_source,
            "utm_medium": tracking_link.utm_medium,
            "utm_campaign": tracking_link.utm_campaign,
            "utm_term": tracking_link.utm_term,
            "utm_content": tracking_link.utm_content
        })
        visitor_doc.insert(ignore_permissions=True)
        visitor = visitor_doc
    
    return visitor

def create_or_update_session(visitor_name, ip_address, user_agent):
    """Create or update visitor session."""
    # Check for existing active session (within last 30 minutes)
    active_session = frappe.db.get_value(
        "Visitor Session",
        {
            "visitor": visitor_name,
            "start_time": [">=", frappe.utils.add_to_date(datetime.now(), minutes=-30)]
        },
        ["name", "page_count"],
        as_dict=True
    )
    
    if active_session:
        # Update existing session
        frappe.db.set_value(
            "Visitor Session",
            active_session.name,
            {
                "last_activity": datetime.now(),
                "page_count": (active_session.page_count or 0) + 1,
                "duration": frappe.db.sql(
                    "SELECT TIMESTAMPDIFF(SECOND, start_time, NOW()) FROM `tabVisitor Session` WHERE name = %s",
                    active_session.name
                )[0][0]
            }
        )
        return frappe.get_doc("Visitor Session", active_session.name)
    else:
        # Create new session
        # Parse user agent
        device_info = parse_user_agent(user_agent)
        location_info = get_location_from_ip(ip_address)
        
        session = frappe.get_doc({
            "doctype": "Visitor Session",
            "visitor": visitor_name,
            "session_id": frappe.generate_hash()[:16],
            "start_time": datetime.now(),
            "last_activity": datetime.now(),
            "ip_address": ip_address,
            "user_agent": user_agent,
            "device_type": device_info.get("device_type"),
            "browser": device_info.get("browser"),
            "operating_system": device_info.get("os"),
            "country": location_info.get("country"),
            "city": location_info.get("city"),
            "page_count": 1,
            "duration": 0
        })
        session.insert(ignore_permissions=True)
        return session

def record_page_view(session_name, tracking_link, referrer):
    """Record page view event."""
    page_view = frappe.get_doc({
        "doctype": "Page View",
        "session": session_name,
        "visitor": frappe.db.get_value("Visitor Session", session_name, "visitor"),
        "tracking_link": tracking_link.name,
        "page_url": tracking_link.destination_url,
        "page_title": tracking_link.link_name,
        "referrer": referrer,
        "timestamp": datetime.now(),
        "time_on_page": 0
    })
    page_view.insert(ignore_permissions=True)
    return page_view

def handle_crm_integration(tracking_link, visitor, session):
    """Handle CRM integration for lead/contact tracking."""
    if tracking_link.link_type == "Lead" and tracking_link.lead:
        # Update lead with tracking info
        lead = frappe.get_doc("Lead", tracking_link.lead)
        if not lead.get("trackflow_visitor_id"):
            lead.trackflow_visitor_id = visitor.visitor_id
            lead.trackflow_first_touch_date = datetime.now()
        lead.trackflow_last_touch_date = datetime.now()
        lead.trackflow_touch_count = (lead.get("trackflow_touch_count") or 0) + 1
        lead.save(ignore_permissions=True)
        
    elif tracking_link.link_type == "Contact" and tracking_link.contact:
        # Update contact with tracking info
        contact = frappe.get_doc("Contact", tracking_link.contact)
        if not contact.get("trackflow_visitor_id"):
            contact.trackflow_visitor_id = visitor.visitor_id
        contact.trackflow_last_campaign = tracking_link.campaign
        contact.save(ignore_permissions=True)
        
    elif tracking_link.link_type == "Deal" and tracking_link.deal:
        # Record deal interaction
        deal = frappe.get_doc("Deal", tracking_link.deal)
        if not deal.get("trackflow_first_touch_source"):
            deal.trackflow_first_touch_source = tracking_link.utm_source
        deal.trackflow_last_touch_source = tracking_link.utm_source
        deal.trackflow_marketing_influenced = 1
        deal.save(ignore_permissions=True)

def build_destination_url(tracking_link, visitor_id):
    """Build destination URL with tracking parameters."""
    url = tracking_link.destination_url
    
    # Parse URL
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    
    # Add UTM parameters if enabled
    if tracking_link.append_utm_params:
        if tracking_link.utm_source:
            query_params["utm_source"] = [tracking_link.utm_source]
        if tracking_link.utm_medium:
            query_params["utm_medium"] = [tracking_link.utm_medium]
        if tracking_link.utm_campaign:
            query_params["utm_campaign"] = [tracking_link.utm_campaign]
        if tracking_link.utm_term:
            query_params["utm_term"] = [tracking_link.utm_term]
        if tracking_link.utm_content:
            query_params["utm_content"] = [tracking_link.utm_content]
    
    # Add visitor ID if enabled
    if tracking_link.append_visitor_id:
        query_params["tf_visitor"] = [visitor_id]
    
    # Rebuild query string
    query_string = "&".join(
        f"{k}={v[0]}" for k, v in query_params.items()
    )
    
    # Rebuild URL
    if query_string:
        url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{query_string}"
    else:
        url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    
    if parsed.fragment:
        url += f"#{parsed.fragment}"
    
    return url

def parse_user_agent(user_agent):
    """Parse user agent string to extract device info."""
    # Simple parser - can be enhanced with proper UA parsing library
    device_info = {
        "device_type": "Desktop",
        "browser": "Unknown",
        "os": "Unknown"
    }
    
    if not user_agent:
        return device_info
    
    ua_lower = user_agent.lower()
    
    # Detect device type
    if "mobile" in ua_lower or "android" in ua_lower:
        device_info["device_type"] = "Mobile"
    elif "tablet" in ua_lower or "ipad" in ua_lower:
        device_info["device_type"] = "Tablet"
    
    # Detect browser
    if "chrome" in ua_lower and "edge" not in ua_lower:
        device_info["browser"] = "Chrome"
    elif "firefox" in ua_lower:
        device_info["browser"] = "Firefox"
    elif "safari" in ua_lower and "chrome" not in ua_lower:
        device_info["browser"] = "Safari"
    elif "edge" in ua_lower:
        device_info["browser"] = "Edge"
    
    # Detect OS
    if "windows" in ua_lower:
        device_info["os"] = "Windows"
    elif "mac" in ua_lower:
        device_info["os"] = "macOS"
    elif "linux" in ua_lower:
        device_info["os"] = "Linux"
    elif "android" in ua_lower:
        device_info["os"] = "Android"
    elif "ios" in ua_lower or "iphone" in ua_lower or "ipad" in ua_lower:
        device_info["os"] = "iOS"
    
    return device_info

def get_location_from_ip(ip_address):
    """Get location info from IP address."""
    # This is a placeholder - implement with actual IP geolocation service
    # For now, return empty location
    return {
        "country": None,
        "city": None
    }

def before_request():
    """Handle tracking before request processing."""
    # Check if this is a tracking pixel request
    if frappe.request.path.startswith("/trackflow/pixel/"):
        return handle_tracking_pixel()

def handle_tracking_pixel():
    """Handle tracking pixel requests."""
    # Return 1x1 transparent pixel
    frappe.response.headers["Content-Type"] = "image/gif"
    frappe.response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    frappe.response.data = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
    return