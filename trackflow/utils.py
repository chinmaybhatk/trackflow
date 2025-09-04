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
            if frappe.db.exists("Visitor", {"visitor_id": visitor_id}):
                visitor = frappe.get_doc("Visitor", {"visitor_id": visitor_id})
                return visitor
        
        # Create new visitor
        visitor = frappe.new_doc("Visitor")
        visitor.visitor_id = generate_visitor_id()
        visitor.first_seen = frappe.utils.now()
        visitor.last_seen = frappe.utils.now()
        visitor.ip_address = frappe.local.request_ip
        
        # Parse user agent for device info
        user_agent = frappe.request.headers.get('User-Agent', '')
        visitor.user_agent = user_agent
        browser, os = parse_user_agent(user_agent)
        visitor.browser = browser
        visitor.operating_system = os
        
        # Determine device type
        if 'Mobile' in user_agent or 'Android' in user_agent or 'iPhone' in user_agent:
            visitor.device_type = 'Mobile'
        elif 'iPad' in user_agent or 'Tablet' in user_agent:
            visitor.device_type = 'Tablet'
        else:
            visitor.device_type = 'Desktop'
        
        # Get geo information if available
        if frappe.local.request_ip:
            geo_info = get_geo_location(frappe.local.request_ip)
            visitor.country = geo_info.get('country')
            visitor.city = geo_info.get('city')
        
        # Get UTM parameters
        visitor.source = frappe.form_dict.get('utm_source', 'direct')
        visitor.medium = frappe.form_dict.get('utm_medium', 'none')
        visitor.campaign = frappe.form_dict.get('utm_campaign')
        visitor.term = frappe.form_dict.get('utm_term')
        visitor.content = frappe.form_dict.get('utm_content')
        
        # Set tracking metrics
        visitor.total_clicks = 0
        visitor.total_sessions = 0
        visitor.total_page_views = 0
        visitor.engagement_score = 0
        
        # Skip internal traffic if configured
        if is_internal_traffic(frappe.local.request_ip):
            return None
        
        # Insert with ignore_permissions to handle guest visitors
        visitor.insert(ignore_permissions=True)
        
        # Set cookie with 1-year expiry (GDPR compliance)
        cookie_options = {
            'expires': (datetime.now() + timedelta(days=365)).strftime('%a, %d %b %Y %H:%M:%S GMT'),
            'path': '/',
            'secure': frappe.request.is_secure,
            'httponly': True,
            'samesite': 'Lax'  # GDPR best practice
        }
        
        frappe.local.cookie_manager.set_cookie(
            'trackflow_visitor', 
            visitor.visitor_id,
            **cookie_options
        )
        
        return visitor
        
    except Exception as e:
        frappe.log_error(f"Error creating visitor: {str(e)}", "TrackFlow Visitor Creation")
        return None


def generate_visitor_id():
    """Generate unique visitor ID"""
    timestamp = datetime.now().isoformat()
    random_str = frappe.generate_hash(length=10)
    return f"v_{hashlib.md5((timestamp + random_str).encode()).hexdigest()[:16]}"


def create_visitor_session(visitor, page_url=None):
    """Create a new visitor session"""
    try:
        # Check if visitor exists
        if not visitor or not isinstance(visitor, frappe.model.document.Document):
            return None
        
        # Create new session
        session = frappe.new_doc("Visitor Session")
        session.visitor = visitor.name
        session.session_id = generate_session_id()
        session.start_time = frappe.utils.now()
        session.ip_address = frappe.local.request_ip
        session.user_agent = frappe.request.headers.get('User-Agent', '')
        
        # Set landing page if provided
        if page_url:
            session.landing_page = sanitize_url(page_url)
        
        # Parse referrer for attribution
        referrer = frappe.request.headers.get('Referer', '')
        if referrer:
            session.referrer = sanitize_url(referrer)
            session.referrer_source = get_referrer_source(referrer)
        
        # Get UTM parameters from request
        session.utm_source = frappe.form_dict.get('utm_source')
        session.utm_medium = frappe.form_dict.get('utm_medium')
        session.utm_campaign = frappe.form_dict.get('utm_campaign')
        session.utm_term = frappe.form_dict.get('utm_term')
        session.utm_content = frappe.form_dict.get('utm_content')
        
        # Initialize metrics
        session.page_views = 1
        session.duration = 0
        
        # Insert session
        session.insert(ignore_permissions=True)
        
        # Update visitor's session count
        visitor.total_sessions = (visitor.total_sessions or 0) + 1
        visitor.last_seen = frappe.utils.now()
        visitor.save(ignore_permissions=True)
        
        # Set session cookie (30-minute expiry for session)
        cookie_options = {
            'expires': (datetime.now() + timedelta(minutes=30)).strftime('%a, %d %b %Y %H:%M:%S GMT'),
            'path': '/',
            'secure': frappe.request.is_secure,
            'httponly': True,
            'samesite': 'Lax'
        }
        
        frappe.local.cookie_manager.set_cookie(
            'trackflow_session', 
            session.session_id,
            **cookie_options
        )
        
        return session
        
    except Exception as e:
        frappe.log_error(f"Error creating visitor session: {str(e)}", "TrackFlow Session Creation")
        return None


def generate_session_id():
    """Generate unique session ID"""
    timestamp = datetime.now().isoformat()
    random_str = frappe.generate_hash(length=10)
    return f"s_{hashlib.md5((timestamp + random_str).encode()).hexdigest()[:16]}"


def get_tracking_script():
    """Get the tracking JavaScript code"""
    settings = frappe.get_cached_doc("TrackFlow Settings", "TrackFlow Settings")
    
    # Check if tracking is enabled
    if not settings or not settings.enable_tracking:
        return "<!-- TrackFlow tracking disabled -->"
    
    # GDPR compliance notice - only include if consent is required
    gdpr_notice = ""
    if settings.require_consent:
        gdpr_notice = """
        // GDPR Compliance
        if (!localStorage.getItem('trackflow_consent')) {
            var consentBanner = document.createElement('div');
            consentBanner.id = 'trackflow-consent';
            consentBanner.style.cssText = 'position:fixed;bottom:0;left:0;right:0;background:#f8f8f8;padding:10px;text-align:center;box-shadow:0 -2px 10px rgba(0,0,0,0.1);z-index:10000;';
            consentBanner.innerHTML = '<p>This site uses cookies to analyze traffic and enhance your experience. <a href="/privacy-policy">Learn more</a></p><button id="trackflow-accept" style="margin:0 10px;padding:5px 15px;background:#4CAF50;color:white;border:none;cursor:pointer;">Accept</button><button id="trackflow-reject" style="padding:5px 15px;background:#f44336;color:white;border:none;cursor:pointer;">Reject</button>';
            document.body.appendChild(consentBanner);
            
            document.getElementById('trackflow-accept').addEventListener('click', function() {
                localStorage.setItem('trackflow_consent', 'granted');
                document.getElementById('trackflow-consent').style.display = 'none';
                // Initialize tracking after consent
                initializeTracking();
            });
            
            document.getElementById('trackflow-reject').addEventListener('click', function() {
                localStorage.setItem('trackflow_consent', 'denied');
                document.getElementById('trackflow-consent').style.display = 'none';
            });
            
            // Don't track until consent is granted
            return;
        }
        
        // Only track if consent was granted
        if (localStorage.getItem('trackflow_consent') !== 'granted') {
            return;
        }
        """
    
    return f"""
    (function() {{
        var tf = window.trackflow = window.trackflow || [];
        tf.push = function() {{
            tf.queue = tf.queue || [];
            tf.queue.push(arguments);
        }};
        
        // Get visitor ID from cookie
        tf.visitor = getCookie('trackflow_visitor');
        tf.session = getCookie('trackflow_session');
        
        function getCookie(name) {{
            var value = "; " + document.cookie;
            var parts = value.split("; " + name + "=");
            if (parts.length == 2) return parts.pop().split(";").shift();
        }}
        
        function initializeTracking() {{
            // Track page view
            tf.push('track', 'pageview', {{
                url: window.location.href,
                title: document.title,
                referrer: document.referrer,
                timestamp: new Date().toISOString()
            }});
            
            // Track clicks on links
            document.addEventListener('click', function(e) {{
                var link = e.target.closest('a');
                if (link && link.href) {{
                    // Skip internal links and anchors
                    if (link.hostname === window.location.hostname && 
                        !link.getAttribute('data-tf-track')) {{
                        return;
                    }}
                    
                    tf.push('track', 'click', {{
                        url: link.href,
                        text: link.innerText || link.textContent,
                        timestamp: new Date().toISOString()
                    }});
                }}
            }});
            
            // Track form submissions
            document.addEventListener('submit', function(e) {{
                var form = e.target;
                if (form && form.getAttribute('data-tf-track')) {{
                    tf.push('track', 'form_submit', {{
                        form_id: form.id || form.getAttribute('data-tf-id') || 'unknown_form',
                        timestamp: new Date().toISOString()
                    }});
                }}
            }});
        }}
        
        {gdpr_notice}
        
        // Initialize tracking if no GDPR requirements or consent already granted
        initializeTracking();
        
        // Load main tracking script
        var script = document.createElement('script');
        script.async = true;
        script.src = '/assets/trackflow/js/trackflow-web.js';
        document.head.appendChild(script);
    }})();
    """


def parse_user_agent(user_agent):
    """Parse user agent string to get browser and OS info"""
    browser = "Unknown"
    os = "Unknown"
    
    # Simple browser detection
    if "Chrome" in user_agent and "Chromium" not in user_agent:
        browser = "Chrome"
    elif "Firefox" in user_agent:
        browser = "Firefox"
    elif "Safari" in user_agent and "Chrome" not in user_agent:
        browser = "Safari"
    elif "Edge" in user_agent or "Edg" in user_agent:
        browser = "Edge"
    elif "Opera" in user_agent or "OPR" in user_agent:
        browser = "Opera"
    elif "MSIE" in user_agent or "Trident" in user_agent:
        browser = "Internet Explorer"
    elif "Chromium" in user_agent:
        browser = "Chromium"
    elif "bot" in user_agent.lower() or "spider" in user_agent.lower() or "crawl" in user_agent.lower():
        browser = "Bot"
        
    # Simple OS detection
    if "Windows" in user_agent:
        os = "Windows"
    elif "Mac" in user_agent:
        os = "macOS"
    elif "Linux" in user_agent and "Android" not in user_agent:
        os = "Linux"
    elif "Android" in user_agent:
        os = "Android"
    elif "iOS" in user_agent or "iPhone" in user_agent or "iPad" in user_agent:
        os = "iOS"
        
    return browser, os


def get_geo_location(ip_address):
    """Get geo location from IP address"""
    try:
        settings = frappe.get_cached_doc("TrackFlow Settings", "TrackFlow Settings")
        
        if settings.geo_ip_service == "None":
            return {
                "country": "Unknown",
                "region": "Unknown",
                "city": "Unknown"
            }
            
        # Placeholder for IP geolocation service integration
        # In a real implementation, you'd call an API service here
        
        # For testing/placeholder, use a basic mapping
        if ip_address.startswith('127.') or ip_address.startswith('192.168.') or ip_address.startswith('10.'):
            return {
                "country": "Internal",
                "region": "Local",
                "city": "Office"
            }
            
        # Default for now - in production, integrate with a real geo service
        return {
            "country": "Unknown",
            "region": "Unknown",
            "city": "Unknown"
        }
        
    except Exception as e:
        frappe.log_error(f"Error in geo location lookup: {str(e)}", "TrackFlow Geo Lookup")
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
    return max(0, min(duration, 3600))  # Cap at 1 hour to avoid outliers


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
    try:
        if not ip_address:
            return False
            
        # Try to get settings
        if not frappe.db.exists("TrackFlow Settings", "TrackFlow Settings"):
            return False
            
        settings = frappe.get_cached_doc("TrackFlow Settings", "TrackFlow Settings")
        
        if not settings.exclude_internal_traffic:
            return False
            
        # Get internal IP ranges
        internal_ips = frappe.get_all(
            "Internal IP Range",
            filters={"parent": "TrackFlow Settings"},
            fields=["ip_range"]
        )
        
        # Check against internal IP ranges
        for ip_range in internal_ips:
            if is_ip_in_range(ip_address, ip_range.ip_range):
                return True
                
        return False
    except:
        # If any error, don't exclude the traffic
        return False


def is_ip_in_range(ip, ip_range):
    """Check if IP is in given range"""
    # Simple implementation - just check prefix match
    # For production, use ipaddress module for proper CIDR handling
    return ip.startswith(ip_range.split('/')[0].strip())


def sanitize_url(url):
    """Sanitize URL for storage"""
    if not url:
        return ""
        
    # Remove sensitive query parameters
    sensitive_params = [
        'password', 'pass', 'pwd', 'passwd',
        'token', 'auth', 'key', 'apikey', 'api_key',
        'secret', 'credentials', 'access_token',
        'code', 'session', 'sessionid', 'session_id'
    ]
    
    try:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        
        # Remove sensitive parameters
        for param in sensitive_params:
            for key in list(params.keys()):
                if param.lower() in key.lower():
                    params.pop(key, None)
                    
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
    except Exception as e:
        # If there's an error parsing the URL, return it unchanged
        # but log the error
        frappe.log_error(f"Error sanitizing URL: {str(e)}", "TrackFlow URL Sanitization")
        return url


def get_referrer_source(referrer_url):
    """Determine source from referrer URL"""
    if not referrer_url:
        return "direct"
        
    try:
        referrer_domain = urlparse(referrer_url).netloc.lower()
        
        # Search engines
        search_engines = {
            'google': 'google',
            'bing': 'bing',
            'yahoo': 'yahoo',
            'duckduckgo': 'duckduckgo',
            'baidu': 'baidu',
            'yandex': 'yandex',
            'ask': 'ask',
            'aol': 'aol'
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
            'youtube': 'youtube',
            'pinterest': 'pinterest',
            'reddit': 'reddit',
            'tumblr': 'tumblr',
            't.co': 'twitter',
            'fb.com': 'facebook',
            'fb.me': 'facebook',
            'lnkd.in': 'linkedin'
        }
        
        for platform, source in social_media.items():
            if platform in referrer_domain:
                return source
                
        # Otherwise, use the domain as source
        return referrer_domain.replace('www.', '')
    except:
        return "direct"


def update_visitor_profile(visitor_id, data):
    """Update visitor profile with new data"""
    try:
        if frappe.db.exists("Visitor", {"visitor_id": visitor_id}):
            visitor = frappe.get_doc("Visitor", {"visitor_id": visitor_id})
            
            # Update fields that are provided
            for key, value in data.items():
                if hasattr(visitor, key):
                    setattr(visitor, key, value)
            
            # Update last seen time
            visitor.last_seen = frappe.utils.now()
            
            # Save visitor data
            visitor.save(ignore_permissions=True)
            return visitor
        else:
            frappe.log_error(f"Visitor not found: {visitor_id}", "TrackFlow Visitor Update")
            return None
    except Exception as e:
        frappe.log_error(f"Error updating visitor profile: {str(e)}", "TrackFlow Visitor Update")
        return None


def create_click_event(tracked_link, visitor_id=None, request_data=None):
    """Create a click event record"""
    try:
        if not tracked_link:
            frappe.log_error("No tracked link provided", "TrackFlow Click Event")
            return None
            
        # Get request data if not provided
        if not request_data:
            request_data = {
                "ip": frappe.local.request_ip,
                "user_agent": frappe.request.headers.get("User-Agent", ""),
                "referrer": frappe.request.headers.get("Referer", "")
            }
            
        # If no visitor ID is provided, get from cookie or generate new
        if not visitor_id:
            visitor_id = frappe.request.cookies.get("trackflow_visitor")
            
            if not visitor_id:
                # Generate new visitor ID
                visitor_id = generate_visitor_id()
                
                # Set cookie with 1-year expiry (GDPR compliance)
                cookie_options = {
                    'expires': (datetime.now() + timedelta(days=365)).strftime('%a, %d %b %Y %H:%M:%S GMT'),
                    'path': '/',
                    'secure': frappe.request.is_secure,
                    'httponly': True,
                    'samesite': 'Lax'
                }
                
                frappe.local.cookie_manager.set_cookie(
                    'trackflow_visitor', 
                    visitor_id,
                    **cookie_options
                )
        
        # Create the click event
        click_event = frappe.new_doc("Click Event")
        click_event.tracked_link = tracked_link.name
        click_event.short_code = tracked_link.short_code
        click_event.campaign = tracked_link.campaign
        click_event.visitor_id = visitor_id
        click_event.click_timestamp = frappe.utils.now()
        
        # Add request data
        click_event.ip_address = request_data.get("ip")
        click_event.user_agent = request_data.get("user_agent", "")
        click_event.referrer = request_data.get("referrer", "")
        
        # Parse user agent
        browser, os = parse_user_agent(request_data.get("user_agent", ""))
        click_event.browser = browser
        click_event.os = os
        
        # Set device type
        if browser == "Bot":
            click_event.device_type = "Bot"
        elif "Mobile" in request_data.get("user_agent", "") or "Android" in request_data.get("user_agent", ""):
            click_event.device_type = "Mobile"
        elif "iPad" in request_data.get("user_agent", "") or "Tablet" in request_data.get("user_agent", ""):
            click_event.device_type = "Tablet"
        else:
            click_event.device_type = "Desktop"
            
        # Geo location
        if request_data.get("ip"):
            geo_info = get_geo_location(request_data.get("ip"))
            click_event.country = geo_info.get("country")
            click_event.region = geo_info.get("region")
            click_event.city = geo_info.get("city")
            
        # Get UTM parameters
        click_event.utm_source = tracked_link.source
        click_event.utm_medium = tracked_link.medium
        
        # Insert the record
        click_event.insert(ignore_permissions=True)
        
        return click_event
    
    except Exception as e:
        frappe.log_error(f"Error creating click event: {str(e)}", "TrackFlow Click Event")
        return None


def generate_short_code(length=6):
    """Generate a unique short code for links"""
    import string
    import random
    
    # Define characters to use (alphanumeric without confusing characters)
    chars = string.ascii_letters + string.digits
    chars = chars.replace('0', '').replace('O', '').replace('I', '').replace('l', '')
    
    # Keep generating until we find a unique code
    while True:
        code = ''.join(random.choice(chars) for _ in range(length))
        
        if not frappe.db.exists("Tracked Link", {"short_code": code}):
            return code


def get_cookie_consent_status():
    """Check the cookie consent status"""
    # From cookie
    consent = frappe.request.cookies.get("trackflow_consent", "unknown")
    
    # From localStorage via JS (would need to be passed from client)
    if consent == "unknown" and frappe.form_dict.get("consent"):
        consent = frappe.form_dict.get("consent")
        
    return consent


def generate_qr_code_data_url(url):
    """Generate a QR code data URL for a link"""
    try:
        import qrcode
        import base64
        from io import BytesIO
        
        # Create QR code instance
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        # Add data
        qr.add_data(url)
        qr.make(fit=True)
        
        # Create an image from the QR Code instance
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to bytes buffer
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        
        # Get the bytes value
        img_bytes = buffer.getvalue()
        
        # Encode to base64
        img_base64 = base64.b64encode(img_bytes).decode()
        
        # Create a data URL
        data_url = f"data:image/png;base64,{img_base64}"
        
        return data_url
    
    except ImportError:
        # If qrcode module is not available, return empty string
        frappe.log_error("QR code library not available. Install 'qrcode' and 'pillow' Python packages.", "TrackFlow QR Code")
        return ""
    except Exception as e:
        frappe.log_error(f"Error generating QR code: {str(e)}", "TrackFlow QR Code")
        return ""


# Jinja methods for templates
def jinja_methods():
    """Methods available in Jinja templates"""
    return {
        "get_tracking_script": get_tracking_script,
        "format_duration": format_duration,
        "get_visitor_from_request": get_visitor_from_request,
        "generate_qr_code_data_url": generate_qr_code_data_url
    }


def jinja_filters():
    """Filters available in Jinja templates"""
    return {
        "format_duration": format_duration,
        "sanitize_url": sanitize_url
    }
