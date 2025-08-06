"""
Redirect handler for tracking links
"""

import frappe
from frappe import _
import json


def before_request():
    """Hook called before processing request"""
    # Check if this is a tracking link
    if frappe.request.path.startswith(("/r/", "/t/")):
        # Will be handled by handle_redirect
        pass


def handle_redirect():
    """Handle redirect for tracking links"""
    try:
        # Get tracking ID from URL
        path_parts = frappe.request.path.split("/")
        if len(path_parts) < 3:
            frappe.throw("Invalid tracking link")
            
        tracking_id = path_parts[2]
        
        # Get tracking link
        if not frappe.db.exists("Tracking Link", tracking_id):
            frappe.throw("Tracking link not found")
            
        tracking_link = frappe.get_doc("Tracking Link", tracking_id)
        
        # Check if link is active
        if tracking_link.status != "Active":
            frappe.throw("This link is no longer active")
            
        # Update click count
        tracking_link.total_clicks = (tracking_link.total_clicks or 0) + 1
        tracking_link.last_accessed = frappe.utils.now()
        tracking_link.last_accessed_ip = frappe.local.request_ip
        tracking_link.save(ignore_permissions=True)
        
        # Track the click event
        track_click_event(tracking_link)
        
        # Get UTM parameters from tracking link
        utm_params = []
        if tracking_link.utm_source:
            utm_params.append(f"utm_source={tracking_link.utm_source}")
        if tracking_link.utm_medium:
            utm_params.append(f"utm_medium={tracking_link.utm_medium}")
        if tracking_link.utm_campaign:
            utm_params.append(f"utm_campaign={tracking_link.campaign}")
        if tracking_link.utm_term:
            utm_params.append(f"utm_term={tracking_link.utm_term}")
        if tracking_link.utm_content:
            utm_params.append(f"utm_content={tracking_link.utm_content}")
            
        # Build destination URL
        destination_url = tracking_link.destination_url
        if utm_params:
            separator = "&" if "?" in destination_url else "?"
            destination_url = f"{destination_url}{separator}{'&'.join(utm_params)}"
            
        # Redirect to destination
        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = destination_url
        
    except Exception as e:
        frappe.log_error(f"Error in tracking redirect: {str(e)}")
        frappe.throw("Error processing tracking link")


def track_click_event(tracking_link):
    """Track the click event"""
    try:
        from trackflow.utils import get_visitor_from_request
        
        # Get or create visitor
        visitor = get_visitor_from_request()
        if not visitor:
            return
            
        # Create click event
        event = frappe.new_doc("Visitor Event")
        event.visitor = visitor.name
        event.event_type = "campaign_click"
        event.event_category = "campaign"
        event.url = tracking_link.destination_url
        event.event_data = json.dumps({
            "tracking_link": tracking_link.name,
            "campaign": tracking_link.campaign,
            "source": tracking_link.utm_source,
            "medium": tracking_link.utm_medium,
            "destination": tracking_link.destination_url
        })
        event.timestamp = frappe.utils.now()
        event.insert(ignore_permissions=True)
        
    except Exception as e:
        frappe.log_error(f"Error tracking click event: {str(e)}")
