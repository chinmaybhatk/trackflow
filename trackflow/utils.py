"""
Utility functions for TrackFlow
"""

import frappe
from frappe import _
import json
import hashlib
from datetime import datetime, timedelta
import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse


def get_visitor_from_request():
    """Get or create visitor from current request"""
    try:
        # Get visitor ID from cookie
        visitor_id = frappe.request.cookies.get('trackflow_visitor')
        
        if visitor_id:
            # Try to get existing visitor
            if frappe.db.exists("Visitor", visitor_id):
                return frappe.get_doc("Visitor", visitor_id)
        
        # Create new visitor
        visitor = frappe.new_doc("Visitor")
        visitor.visitor_id = generate_visitor_id()
        visitor.first_seen = frappe.utils.now()
        visitor.last_seen = frappe.utils.now()
        visitor.ip_address = frappe.local.request_ip
        visitor.user_agent = frappe.request.headers.get('User-Agent', '')
        
        # Get UTM parameters
        visitor.source = frappe.form_dict.get('utm_source', 'direct')
        visitor.medium = frappe.form_dict.get('utm_medium', 'none')
        visitor.campaign = frappe.form_dict.get('utm_campaign')
        visitor.term = frappe.form_dict.get('utm_term')
        visitor.content = frappe.form_dict.get('utm_content')
        
        visitor.insert(ignore_permissions=True)
        
        # Set cookie
        frappe.local.cookie_manager.set_cookie('trackflow_visitor', visitor.visitor_id)
        
        return visitor
        
    except Exception as e:
        frappe.log_error(f"Error creating visitor: {str(e)}")
        return None


def generate_visitor_id():
    """Generate unique visitor ID"""
    timestamp = datetime.now().isoformat()
    random_str = frappe.generate_hash(length=10)
    return f"v_{hashlib.md5((timestamp + random_str).encode()).hexdigest()[:16]}"


def create_visitor_session(visitor, page_url=None):
    """Create a new visitor session"""
    try:
        session = frappe.new_doc("Visitor Session")
        session.visitor = visitor.name
        session.session_id = generate_session_id()
        session.start_time = frappe.utils.now()
        session.ip_address = frappe.local.request_ip
        session.user_agent = frappe.request.headers.get('User-Agent', '')
        
        if page_url:
            session.landing_page = page_url
            
        session.insert(ignore_permissions=True)
        return session
        
    except Exception as e:
        frappe.log_error(f"Error creating visitor session: {str(e)}")
        return None


def generate_session_id():
    """Generate unique session ID"""
    timestamp = datetime.now().isoformat()
    random_str = frappe.generate_hash(length=10)
    return f"s_{hashlib.md5((timestamp + random_str).encode()).hexdigest()[:16]}"


def get_tracking_script():
    """Get the tracking JavaScript code"""
    return """
    (function() {
        var tf = window.trackflow = window.trackflow || [];
        tf.push = function() {
            tf.queue = tf.queue || [];
            tf.queue.push(arguments);
        };
        tf.visitor = getCookie('trackflow_visitor');
        
        function getCookie(name) {
            var value = "; " + document.cookie;
            var parts = value.split("; " + name + "=");
            if (parts.length == 2) return parts.pop().split(";").shift();
        }
        
        // Track page view
        tf.push('track', 'pageview', {
            url: window.location.href,
            title: document.title,
            referrer: document.referrer
        });
        
        // Load tracking script
        var script = document.createElement('script');
        script.async = true;
        script.src = '/assets/trackflow/js/trackflow-web.js';
        document.head.appendChild(script);
    })();
    """


def parse_user_agent(user_agent):
    """Parse user agent string to get browser and OS info"""
    browser = "Unknown"
    os = "Unknown"
    
    # Simple browser detection
    if "Chrome" in user_agent:
        browser = "Chrome"
    elif "Firefox" in user_agent:
        browser = "Firefox"
    elif "Safari" in user_agent:
        browser = "Safari"
    elif "Edge" in user_agent:
        browser = "Edge"
    elif "Opera" in user_agent:
        browser = "Opera"
        
    # Simple OS detection
    if "Windows" in user_agent:
        os = "Windows"
    elif "Mac" in user_agent:
        os = "macOS"
    elif "Linux" in user_agent:
        os = "Linux"
    elif "Android" in user_agent:
        os = "Android"
    elif "iOS" in user_agent or "iPhone" in user_agent:
        os = "iOS"
        
    return browser, os


def get_geo_location(ip_address):
    """Get geo location from IP address"""
    # This is a placeholder - you would integrate with a geo IP service
    return {
        "country": "Unknown",
        "region": "Unknown",
        "city": "Unknown"
    }


def calculate_time_on_page(start_time, end_time):
    """Calculate time spent on page in seconds"""
    if not start_time or not end_time:
        return 0
        
    start = frappe.utils.get_datetime(start_time)
    end = frappe.utils.get_datetime(end_time)
    
    duration = (end - start).total_seconds()
    return max(0, duration)  # Ensure non-negative


def format_duration(seconds):
    """Format duration in human readable format"""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes}m"
    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}h {minutes}m"


def get_bounce_rate(visitor):
    """Calculate bounce rate for a visitor"""
    if not visitor:
        return 0
        
    sessions = frappe.get_all(
        "Visitor Session",
        filters={"visitor": visitor.name},
        fields=["page_views"]
    )
    
    if not sessions:
        return 0
        
    single_page_sessions = sum(1 for s in sessions if (s.page_views or 0) <= 1)
    bounce_rate = (single_page_sessions / len(sessions)) * 100
    
    return round(bounce_rate, 2)


def is_internal_traffic(ip_address):
    """Check if IP address is internal traffic"""
    settings = frappe.get_single("TrackFlow Settings")
    
    if not settings.exclude_internal_traffic:
        return False
        
    # Check against internal IP ranges
    for ip_range in settings.internal_ip_ranges:
        if is_ip_in_range(ip_address, ip_range.ip_range):
            return True
            
    return False


def is_ip_in_range(ip, ip_range):
    """Check if IP is in given range"""
    # Simple implementation - you might want to use ipaddress module
    return ip.startswith(ip_range)


def sanitize_url(url):
    """Sanitize URL for storage"""
    if not url:
        return ""
        
    # Remove sensitive query parameters
    sensitive_params = ['password', 'token', 'key', 'secret']
    
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    
    # Remove sensitive parameters
    for param in sensitive_params:
        params.pop(param, None)
        
    # Reconstruct URL
    clean_query = urlencode(params, doseq=True)
    clean_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        clean_query,
        parsed.fragment
    ))
    
    return clean_url


def get_referrer_source(referrer_url):
    """Determine source from referrer URL"""
    if not referrer_url:
        return "direct"
        
    referrer_domain = urlparse(referrer_url).netloc.lower()
    
    # Search engines
    search_engines = {
        'google': 'google',
        'bing': 'bing',
        'yahoo': 'yahoo',
        'duckduckgo': 'duckduckgo',
        'baidu': 'baidu'
    }
    
    for engine, source in search_engines.items():
        if engine in referrer_domain:
            return source
            
    # Social media
    social_media = {
        'facebook': 'facebook',
        'twitter': 'twitter',
        'linkedin': 'linkedin',
        'instagram': 'instagram',
        'youtube': 'youtube'
    }
    
    for platform, source in social_media.items():
        if platform in referrer_domain:
            return source
            
    # Otherwise, use the domain as source
    return referrer_domain.replace('www.', '')


def update_visitor_profile(visitor_id, data):
    """Update visitor profile with new data"""
    try:
        if frappe.db.exists("Visitor", visitor_id):
            visitor = frappe.get_doc("Visitor", visitor_id)
            for key, value in data.items():
                if hasattr(visitor, key):
                    setattr(visitor, key, value)
            visitor.save(ignore_permissions=True)
            return visitor
    except Exception as e:
        frappe.log_error(f"Error updating visitor profile: {str(e)}")
        return None


# Jinja methods for templates
def jinja_methods():
    """Methods available in Jinja templates"""
    return {
        "get_tracking_script": get_tracking_script,
        "format_duration": format_duration,
        "get_visitor_from_request": get_visitor_from_request
    }


def jinja_filters():
    """Filters available in Jinja templates"""
    return {
        "format_duration": format_duration,
        "sanitize_url": sanitize_url
    }
