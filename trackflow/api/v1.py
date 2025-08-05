"""
TrackFlow REST API v1
"""

import frappe
from frappe import _
from frappe.utils import cint, get_url, now_datetime
import json
from urllib.parse import urlencode

@frappe.whitelist(allow_guest=True)
def track_click(short_code=None):
    """
    Track a click on a short link
    Called when someone visits /tl/SHORT_CODE
    """
    if not short_code:
        frappe.throw(_("Invalid link"))
    
    # Get the tracked link
    try:
        link = frappe.get_doc("Tracked Link", {"short_code": short_code})
    except frappe.DoesNotExistError:
        frappe.throw(_("Link not found"), frappe.DoesNotExistError)
    
    # Check if link is active
    if link.status != "Active":
        if link.status == "Expired":
            frappe.throw(_("This link has expired"))
        else:
            frappe.throw(_("This link is no longer active"))
    
    # Get request details
    request_data = get_request_details()
    
    # Queue the click for processing
    queue_click_event(link, request_data)
    
    # Build final URL with UTM parameters
    final_url = build_final_url(link)
    
    # Redirect to final URL
    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = final_url
    
    return

@frappe.whitelist()
def create_link(url, campaign=None, custom_alias=None, **kwargs):
    """
    Create a new tracked link
    """
    # Validate URL
    if not url or not url.startswith(('http://', 'https://')):
        frappe.throw(_("Please provide a valid URL"))
    
    # Create tracked link document
    link = frappe.new_doc("Tracked Link")
    link.target_url = url
    link.link_campaign = campaign
    link.custom_alias = custom_alias
    
    # Set UTM parameters if provided
    for param in ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content']:
        if kwargs.get(param):
            setattr(link, param, kwargs[param])
    
    # Set additional options
    if kwargs.get('expiry_date'):
        link.expiry_date = kwargs['expiry_date']
    
    if kwargs.get('tags'):
        link.tags = kwargs['tags']
    
    link.insert()
    
    return {
        "success": True,
        "short_url": link.short_url,
        "short_code": link.short_code,
        "tracking_url": link.get_tracking_url()
    }

@frappe.whitelist()
def get_analytics(short_code=None, campaign=None, period="7d"):
    """
    Get analytics for a link or campaign
    """
    filters = {}
    
    if short_code:
        link = frappe.get_doc("Tracked Link", {"short_code": short_code})
        filters["tracked_link"] = link.name
    elif campaign:
        filters["link_campaign"] = campaign
    else:
        frappe.throw(_("Please provide either short_code or campaign"))
    
    # Get date range
    date_range = get_date_range(period)
    filters["timestamp"] = ["between", date_range]
    
    # Get click events
    clicks = frappe.get_all(
        "Click Event",
        filters=filters,
        fields=[
            "timestamp",
            "country",
            "city",
            "browser",
            "device_type",
            "referrer_domain"
        ],
        order_by="timestamp desc"
    )
    
    # Calculate analytics
    analytics = calculate_analytics(clicks)
    
    return {
        "success": True,
        "period": period,
        "data": analytics,
        "clicks": clicks[:100]  # Return latest 100 clicks
    }

@frappe.whitelist()
def track_conversion(short_code, conversion_value=0, conversion_type="sale"):
    """
    Track a conversion from a tracked link
    """
    # Get the link
    link = frappe.get_doc("Tracked Link", {"short_code": short_code})
    
    # Create conversion record
    conversion = frappe.new_doc("Link Conversion")
    conversion.tracked_link = link.name
    conversion.conversion_type = conversion_type
    conversion.conversion_value = conversion_value
    conversion.timestamp = now_datetime()
    
    # Try to match with a lead/contact
    if frappe.session.user != "Guest":
        conversion.user = frappe.session.user
        
        # Check if user is a lead or contact
        if frappe.db.exists("Contact", {"email_id": frappe.session.user}):
            conversion.contact = frappe.db.get_value("Contact", 
                {"email_id": frappe.session.user}, "name")
        elif frappe.db.exists("Lead", {"email_id": frappe.session.user}):
            conversion.lead = frappe.db.get_value("Lead", 
                {"email_id": frappe.session.user}, "name")
    
    conversion.insert(ignore_permissions=True)
    
    # Update link stats
    link.total_conversions = (link.total_conversions or 0) + 1
    link.total_conversion_value = (link.total_conversion_value or 0) + conversion_value
    link.save(ignore_permissions=True)
    
    return {
        "success": True,
        "message": _("Conversion tracked successfully")
    }

@frappe.whitelist()
def bulk_create_links(links):
    """
    Create multiple tracked links at once
    """
    if isinstance(links, str):
        links = json.loads(links)
    
    created_links = []
    errors = []
    
    for link_data in links:
        try:
            result = create_link(**link_data)
            created_links.append(result)
        except Exception as e:
            errors.append({
                "url": link_data.get("url"),
                "error": str(e)
            })
    
    return {
        "success": len(errors) == 0,
        "created": len(created_links),
        "links": created_links,
        "errors": errors
    }

def get_request_details():
    """
    Extract request details for tracking
    """
    request = frappe.local.request
    
    return {
        "ip_address": request.headers.get('X-Forwarded-For', request.remote_addr),
        "user_agent": request.headers.get('User-Agent', ''),
        "referrer": request.headers.get('Referer', ''),
        "language": request.headers.get('Accept-Language', '').split(',')[0],
        "timestamp": now_datetime()
    }

def queue_click_event(link, request_data):
    """
    Queue click event for async processing
    """
    # Parse user agent for device info
    device_info = parse_user_agent(request_data.get('user_agent', ''))
    
    # Get geo info from IP (if service is configured)
    geo_info = get_geo_info(request_data.get('ip_address', ''))
    
    # Create queue entry
    queue_entry = frappe.new_doc("Click Queue")
    queue_entry.tracked_link = link.name
    queue_entry.timestamp = request_data['timestamp']
    queue_entry.ip_address = request_data['ip_address']
    queue_entry.user_agent = request_data['user_agent']
    queue_entry.referrer = request_data.get('referrer', '')
    queue_entry.browser = device_info.get('browser', '')
    queue_entry.device_type = device_info.get('device_type', '')
    queue_entry.os = device_info.get('os', '')
    queue_entry.country = geo_info.get('country', '')
    queue_entry.city = geo_info.get('city', '')
    queue_entry.status = "Pending"
    
    queue_entry.insert(ignore_permissions=True)
    frappe.db.commit()

def build_final_url(link):
    """
    Build final URL with UTM parameters
    """
    url = link.target_url
    
    # Add UTM parameters
    utm_params = {}
    for param in ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content']:
        value = getattr(link, param, None)
        if value:
            utm_params[param] = value
    
    if utm_params:
        # Check if URL already has parameters
        separator = '&' if '?' in url else '?'
        url += separator + urlencode(utm_params)
    
    return url

def parse_user_agent(user_agent_string):
    """
    Parse user agent string to extract device info
    """
    # Simple implementation - in production, use a proper UA parser
    device_info = {
        'browser': 'Unknown',
        'device_type': 'Desktop',
        'os': 'Unknown'
    }
    
    ua_lower = user_agent_string.lower()
    
    # Detect browser
    if 'chrome' in ua_lower:
        device_info['browser'] = 'Chrome'
    elif 'firefox' in ua_lower:
        device_info['browser'] = 'Firefox'
    elif 'safari' in ua_lower:
        device_info['browser'] = 'Safari'
    elif 'edge' in ua_lower:
        device_info['browser'] = 'Edge'
    
    # Detect device type
    if 'mobile' in ua_lower:
        device_info['device_type'] = 'Mobile'
    elif 'tablet' in ua_lower:
        device_info['device_type'] = 'Tablet'
    
    # Detect OS
    if 'windows' in ua_lower:
        device_info['os'] = 'Windows'
    elif 'mac' in ua_lower:
        device_info['os'] = 'macOS'
    elif 'linux' in ua_lower:
        device_info['os'] = 'Linux'
    elif 'android' in ua_lower:
        device_info['os'] = 'Android'
    elif 'ios' in ua_lower or 'iphone' in ua_lower:
        device_info['os'] = 'iOS'
    
    return device_info

def get_geo_info(ip_address):
    """
    Get geographical information from IP address
    """
    # Placeholder - implement with actual geo service
    return {
        'country': 'Unknown',
        'city': 'Unknown',
        'region': 'Unknown'
    }

def get_date_range(period):
    """
    Convert period string to date range
    """
    from frappe.utils import add_days, get_datetime
    
    end_date = get_datetime()
    
    if period == "1d":
        start_date = add_days(end_date, -1)
    elif period == "7d":
        start_date = add_days(end_date, -7)
    elif period == "30d":
        start_date = add_days(end_date, -30)
    elif period == "90d":
        start_date = add_days(end_date, -90)
    else:
        start_date = add_days(end_date, -7)  # Default to 7 days
    
    return [start_date, end_date]

def calculate_analytics(clicks):
    """
    Calculate analytics from click data
    """
    from collections import defaultdict
    
    analytics = {
        "total_clicks": len(clicks),
        "unique_visitors": len(set(c.get('ip_address') for c in clicks)),
        "countries": defaultdict(int),
        "browsers": defaultdict(int),
        "devices": defaultdict(int),
        "referrers": defaultdict(int),
        "daily_clicks": defaultdict(int)
    }
    
    for click in clicks:
        # Country distribution
        country = click.get('country', 'Unknown')
        analytics['countries'][country] += 1
        
        # Browser distribution
        browser = click.get('browser', 'Unknown')
        analytics['browsers'][browser] += 1
        
        # Device distribution
        device = click.get('device_type', 'Unknown')
        analytics['devices'][device] += 1
        
        # Referrer distribution
        referrer = click.get('referrer_domain', 'Direct')
        analytics['referrers'][referrer] += 1
        
        # Daily clicks
        date = click.get('timestamp').date() if click.get('timestamp') else None
        if date:
            analytics['daily_clicks'][str(date)] += 1
    
    # Convert defaultdicts to regular dicts
    for key in ['countries', 'browsers', 'devices', 'referrers', 'daily_clicks']:
        analytics[key] = dict(analytics[key])
    
    return analytics