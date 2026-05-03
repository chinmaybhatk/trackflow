from .error_handler import (
    handle_error,
    validate_required_fields,
    validate_url,
    sanitize_input,
    get_client_ip,
    rate_limit_check,
    is_internal_ip,
    log_activity,
    TrackFlowError,
    ValidationError,
    ConfigurationError,
    TrackingError,
    IntegrationError,
)

import frappe
import hashlib
from datetime import datetime


def generate_visitor_id():
    """Generate unique visitor ID"""
    timestamp = datetime.now().isoformat()
    random_str = frappe.generate_hash(length=10)
    return f"v_{hashlib.md5((timestamp + random_str).encode()).hexdigest()[:16]}"


def create_click_event(tracked_link, visitor_id, request_data=None):
    """Create a click event record for a tracked link"""
    try:
        click_event = frappe.new_doc("Click Event")
        click_event.tracked_link = tracked_link.name
        click_event.short_code = tracked_link.short_code
        click_event.visitor_id = visitor_id
        click_event.event_type = "click"
        click_event.click_timestamp = frappe.utils.now()

        if request_data:
            click_event.ip_address = request_data.get("ip")
            click_event.user_agent = request_data.get("user_agent")
            click_event.referrer = request_data.get("referrer")

        if tracked_link.campaign:
            click_event.campaign = tracked_link.campaign

        if tracked_link.source:
            click_event.utm_source = tracked_link.source
        if tracked_link.medium:
            click_event.utm_medium = tracked_link.medium

        click_event.insert(ignore_permissions=True)
        return click_event

    except Exception as e:
        frappe.log_error(f"Error creating click event: {str(e)}", "TrackFlow Click Event")
        return None


def get_visitor_from_request(request=None):
    """Get or create visitor from HTTP request"""
    if not request:
        request = getattr(frappe.local, "request", None)
    if not request:
        return None, None

    visitor_id = request.cookies.get("trackflow_visitor")

    if not visitor_id:
        visitor_id = generate_visitor_id()

    if frappe.db.exists("Visitor", {"visitor_id": visitor_id}):
        visitor_name = frappe.db.get_value("Visitor", {"visitor_id": visitor_id}, "name")
    else:
        visitor_doc = frappe.new_doc("Visitor")
        visitor_doc.visitor_id = visitor_id
        visitor_doc.first_seen = frappe.utils.now()
        visitor_doc.last_seen = frappe.utils.now()
        visitor_doc.ip_address = get_client_ip()
        visitor_doc.user_agent = request.headers.get("User-Agent", "")
        visitor_doc.insert(ignore_permissions=True)
        visitor_name = visitor_doc.name

    return visitor_id, visitor_name


def set_visitor_cookie(response, visitor_id):
    """Set visitor tracking cookie"""
    try:
        settings = frappe.get_single("TrackFlow Settings")
        expires_days = getattr(settings, "cookie_expires_days", 365)
    except Exception:
        expires_days = 365

    response.set_cookie(
        "trackflow_visitor",
        visitor_id,
        max_age=expires_days * 24 * 60 * 60,
        secure=frappe.local.request.scheme == "https" if frappe.local.request else False,
        httponly=False,
        samesite="Lax",
    )


def parse_user_agent(user_agent):
    """Parse user agent string to extract browser, OS, device info"""
    browser = "Unknown"
    os_name = "Unknown"
    device = "Desktop"

    if user_agent:
        ua = user_agent.lower()

        if "chrome" in ua and "edg" not in ua:
            browser = "Chrome"
        elif "firefox" in ua:
            browser = "Firefox"
        elif "edg" in ua:
            browser = "Edge"
        elif "safari" in ua:
            browser = "Safari"
        elif "opera" in ua or "opr" in ua:
            browser = "Opera"

        if "windows" in ua:
            os_name = "Windows"
        elif "mac" in ua:
            os_name = "macOS"
        elif "android" in ua:
            os_name = "Android"
        elif "iphone" in ua or "ipad" in ua:
            os_name = "iOS"
        elif "linux" in ua:
            os_name = "Linux"

        if "mobile" in ua or "android" in ua and "tablet" not in ua:
            device = "Mobile"
        elif "tablet" in ua or "ipad" in ua:
            device = "Tablet"

    return {"browser": browser, "os": os_name, "device": device}
