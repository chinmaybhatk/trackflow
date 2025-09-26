# Import utility functions for easier access
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
    IntegrationError
)

import frappe
import uuid
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
        # Get or create visitor
        visitor = None
        if frappe.db.exists("Visitor", {"visitor_id": visitor_id}):
            visitor = frappe.db.get_value("Visitor", {"visitor_id": visitor_id}, "name")
        else:
            # Create new visitor
            visitor_doc = frappe.new_doc("Visitor")
            visitor_doc.visitor_id = visitor_id
            visitor_doc.first_seen = frappe.utils.now()
            visitor_doc.last_seen = frappe.utils.now()
            
            if request_data:
                visitor_doc.ip_address = request_data.get("ip")
                visitor_doc.user_agent = request_data.get("user_agent")
            
            visitor_doc.insert(ignore_permissions=True)
            visitor = visitor_doc.name
        
        # Create click event
        click_event = frappe.new_doc("Click Event")
        click_event.tracked_link = tracked_link.name
        click_event.visitor_id = visitor_id
        click_event.visitor = visitor
        click_event.timestamp = frappe.utils.now()
        
        if request_data:
            click_event.ip_address = request_data.get("ip")
            click_event.user_agent = request_data.get("user_agent")
            click_event.referrer = request_data.get("referrer")
        
        # Add campaign information from tracked link
        if tracked_link.campaign:
            click_event.campaign = tracked_link.campaign
        
        click_event.insert(ignore_permissions=True)
        return click_event
        
    except Exception as e:
        frappe.log_error(f"Error creating click event: {str(e)}", "TrackFlow Click Event")
        return None

def get_visitor_from_request():
    """Get visitor ID from request (cookies or headers)"""
    visitor_id = None
    
    if frappe.request:
        # Check cookies - using consistent cookie name
        visitor_id = frappe.request.cookies.get('trackflow_visitor')
        
        # Check headers (for API requests)
        if not visitor_id:
            visitor_id = frappe.request.headers.get('X-TrackFlow-Visitor-ID')
    
    return visitor_id

def get_visitor_from_request(request=None):
    """Get or create visitor from HTTP request"""
    if not request:
        request = frappe.local.request
    
    # Try to get visitor ID from cookie
    visitor_id = request.cookies.get('trackflow_visitor_id')
    
    if not visitor_id:
        # Generate new visitor ID
        visitor_id = generate_visitor_id()
    
    # Get or create visitor record
    if frappe.db.exists("Visitor", {"visitor_id": visitor_id}):
        visitor_name = frappe.db.get_value("Visitor", {"visitor_id": visitor_id}, "name")
    else:
        # Create new visitor
        visitor_doc = frappe.new_doc("Visitor")
        visitor_doc.visitor_id = visitor_id
        visitor_doc.first_seen = frappe.utils.now()
        visitor_doc.last_seen = frappe.utils.now()
        visitor_doc.ip_address = get_client_ip()
        visitor_doc.user_agent = request.headers.get('User-Agent', '')
        visitor_doc.insert(ignore_permissions=True)
        visitor_name = visitor_doc.name
    
    return visitor_id, visitor_name

def set_visitor_cookie(response, visitor_id):
    """Set visitor tracking cookie"""
    # Get cookie expiration from settings
    try:
        settings = frappe.get_single("TrackFlow Settings")
        expires_days = getattr(settings, 'cookie_expires_days', 365)
    except:
        expires_days = 365
    
    response.set_cookie(
        'trackflow_visitor_id',
        visitor_id,
        max_age=expires_days * 24 * 60 * 60,  # Convert days to seconds
        secure=frappe.local.request.scheme == 'https',
        httponly=False,  # Allow JavaScript access for client-side tracking
        samesite='Lax'
    )

def parse_user_agent(user_agent):
    """Parse user agent string to extract browser, OS, device info"""
    # Simple user agent parsing - could be enhanced with a library
    browser = "Unknown"
    os = "Unknown"
    device = "Desktop"
    
    if user_agent:
        user_agent = user_agent.lower()
        
        # Browser detection
        if 'chrome' in user_agent:
            browser = "Chrome"
        elif 'firefox' in user_agent:
            browser = "Firefox"
        elif 'safari' in user_agent:
            browser = "Safari"
        elif 'edge' in user_agent:
            browser = "Edge"
        elif 'opera' in user_agent:
            browser = "Opera"
        
        # OS detection
        if 'windows' in user_agent:
            os = "Windows"
        elif 'mac' in user_agent:
            os = "macOS"
        elif 'linux' in user_agent:
            os = "Linux"
        elif 'android' in user_agent:
            os = "Android"
        elif 'ios' in user_agent:
            os = "iOS"
        
        # Device detection
        if 'mobile' in user_agent or 'android' in user_agent:
            device = "Mobile"
        elif 'tablet' in user_agent or 'ipad' in user_agent:
            device = "Tablet"
    
    return {
        "browser": browser,
        "os": os,
        "device": device
    }

def check_gdpr_consent(visitor_id):
    """Check if visitor has given GDPR consent"""
    # Simple check - could be enhanced based on requirements
    return frappe.db.get_value("Visitor", {"visitor_id": visitor_id}, "gdpr_consent") or False

def record_gdpr_consent(visitor_id, consent=True):
    """Record GDPR consent for visitor"""
    if frappe.db.exists("Visitor", {"visitor_id": visitor_id}):
        frappe.db.set_value("Visitor", {"visitor_id": visitor_id}, {
            "gdpr_consent": consent,
            "gdpr_consent_date": frappe.utils.now()
        })
