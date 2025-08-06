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
        
        # Check if tracking link exists - using "Tracked Link" instead of "Tracking Link"
        if not frappe.db.exists("Tracked Link", tracking_id):
            frappe.throw("Tracking link not found")
            
        tracking_link = frappe.get_doc("Tracked Link", tracking_id)
        
        # Check if link is active
        if tracking_link.status != "Active":
            frappe.throw("This link is no longer active")
            
        # Update click count
        tracking_link.click_count = (tracking_link.click_count or 0) + 1
        tracking_link.last_clicked = frappe.utils.now()
        tracking_link.save(ignore_permissions=True)
        
        # Track the click event
        track_click_event(tracking_link)
        
        # Get target URL - it's called target_url in the schema
        destination_url = tracking_link.target_url or ""
        
        # If no target URL override, get from campaign
        if not destination_url and tracking_link.campaign:
            try:
                campaign = frappe.get_doc("Link Campaign", tracking_link.campaign)
                # Assuming campaign has a target_url field
                destination_url = getattr(campaign, "target_url", "")
            except:
                pass
        
        if not destination_url:
            frappe.throw("No destination URL configured")
        
        # Apply UTM parameters from override or campaign
        utm_params = []
        
        # Try to parse UTM override
        if tracking_link.utm_override:
            try:
                utm_data = json.loads(tracking_link.utm_override)
                for key, value in utm_data.items():
                    if key.startswith("utm_") and value:
                        utm_params.append(f"{key}={value}")
            except:
                pass
        
        # Build destination URL with UTM params
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
        # For now, we'll use Click Event DocType which exists
        event = frappe.new_doc("Click Event")
        
        # Map fields based on what Click Event might have
        event.tracked_link = tracking_link.name
        event.click_time = frappe.utils.now()
        
        # Try to get visitor info from cookies (even though Visitor DocType doesn't exist)
        visitor_id = frappe.request.cookies.get('trackflow_visitor')
        if visitor_id:
            event.visitor_id = visitor_id
        
        # Save click event
        event.insert(ignore_permissions=True)
        
    except Exception as e:
        frappe.log_error(f"Error tracking click event: {str(e)}")
