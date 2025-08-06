"""
Jinja filters for TrackFlow templates
"""

import frappe
from frappe import _
from datetime import datetime, timedelta
import json


def timeago(timestamp):
    """Convert timestamp to time ago format"""
    if not timestamp:
        return "Never"
        
    now = frappe.utils.now_datetime()
    if isinstance(timestamp, str):
        timestamp = frappe.utils.get_datetime(timestamp)
        
    diff = now - timestamp
    
    if diff.days > 365:
        return f"{diff.days // 365} year{'s' if diff.days // 365 > 1 else ''} ago"
    elif diff.days > 30:
        return f"{diff.days // 30} month{'s' if diff.days // 30 > 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        return f"{diff.seconds // 3600} hour{'s' if diff.seconds // 3600 > 1 else ''} ago"
    elif diff.seconds > 60:
        return f"{diff.seconds // 60} minute{'s' if diff.seconds // 60 > 1 else ''} ago"
    else:
        return "Just now"


def humanize_number(value):
    """Convert large numbers to human readable format"""
    if not value:
        return "0"
        
    value = float(value)
    
    if value >= 1000000:
        return f"{value/1000000:.1f}M"
    elif value >= 1000:
        return f"{value/1000:.1f}K"
    else:
        return str(int(value))


def percentage(value, total):
    """Calculate percentage"""
    if not total or total == 0:
        return "0%"
        
    pct = (float(value) / float(total)) * 100
    return f"{pct:.1f}%"


def json_dumps(value):
    """Safely dump JSON"""
    try:
        return json.dumps(value)
    except:
        return "{}"


def truncate_url(url, length=50):
    """Truncate URL for display"""
    if not url or len(url) <= length:
        return url
        
    # Remove protocol
    display_url = url.replace("https://", "").replace("http://", "")
    
    if len(display_url) <= length:
        return display_url
        
    # Truncate and add ellipsis
    return display_url[:length-3] + "..."


def format_date_range(start_date, end_date):
    """Format date range for display"""
    if not start_date:
        return "All time"
        
    start = frappe.utils.get_datetime(start_date)
    end = frappe.utils.get_datetime(end_date) if end_date else frappe.utils.now_datetime()
    
    if start.date() == end.date():
        return start.strftime("%B %d, %Y")
    elif start.year == end.year:
        if start.month == end.month:
            return f"{start.strftime('%B %d')} - {end.strftime('%d, %Y')}"
        else:
            return f"{start.strftime('%B %d')} - {end.strftime('%B %d, %Y')}"
    else:
        return f"{start.strftime('%B %d, %Y')} - {end.strftime('%B %d, %Y')}"


def device_type(user_agent):
    """Determine device type from user agent"""
    if not user_agent:
        return "Unknown"
        
    ua_lower = user_agent.lower()
    
    if "mobile" in ua_lower or "android" in ua_lower or "iphone" in ua_lower:
        return "Mobile"
    elif "tablet" in ua_lower or "ipad" in ua_lower:
        return "Tablet"
    else:
        return "Desktop"


def clean_referrer(referrer_url):
    """Clean referrer URL for display"""
    if not referrer_url:
        return "Direct"
        
    # Remove protocol and www
    clean = referrer_url.replace("https://", "").replace("http://", "").replace("www.", "")
    
    # Remove trailing slash
    if clean.endswith("/"):
        clean = clean[:-1]
        
    # Extract domain only
    parts = clean.split("/")
    if parts:
        return parts[0]
        
    return clean


def format_bounce_rate(rate):
    """Format bounce rate for display"""
    if rate is None:
        return "N/A"
        
    return f"{float(rate):.1f}%"


def utm_campaign_name(campaign_id):
    """Get campaign name from ID"""
    if not campaign_id:
        return "No Campaign"
        
    try:
        return frappe.get_value("Campaign", campaign_id, "campaign_name") or campaign_id
    except:
        return campaign_id


def highlight_search(text, search_term):
    """Highlight search term in text"""
    if not text or not search_term:
        return text
        
    import re
    pattern = re.compile(re.escape(search_term), re.IGNORECASE)
    return pattern.sub(f'<mark>{search_term}</mark>', str(text))


def format_file_size(size_in_bytes):
    """Format file size in human readable format"""
    if not size_in_bytes:
        return "0 B"
        
    size = float(size_in_bytes)
    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
        
    return f"{size:.1f} {units[unit_index]}"


def pluralize(count, singular, plural=None):
    """Pluralize word based on count"""
    if not plural:
        plural = singular + "s"
        
    return singular if count == 1 else plural


def format_tracking_link(link_id, base_url=None):
    """Format complete tracking link URL"""
    if not base_url:
        base_url = frappe.utils.get_url()
        
    return f"{base_url}/r/{link_id}"


def obfuscate_ip(ip_address):
    """Obfuscate IP address for privacy"""
    if not ip_address:
        return "Unknown"
        
    parts = ip_address.split(".")
    if len(parts) == 4:
        # Hide last octet for privacy
        return f"{parts[0]}.{parts[1]}.{parts[2]}.xxx"
    else:
        # IPv6 - hide last segments
        return ip_address[:len(ip_address)//2] + "..."


def format_duration_mins(seconds):
    """Format duration in minutes and seconds"""
    if not seconds:
        return "0s"
        
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    
    if mins > 0:
        return f"{mins}m {secs}s"
    else:
        return f"{secs}s"
