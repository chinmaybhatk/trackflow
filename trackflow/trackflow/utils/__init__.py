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
