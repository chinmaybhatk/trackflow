"""
TrackFlow utility functions
"""

import frappe
from frappe import _
from datetime import timedelta


def format_duration(seconds):
    """Format duration in seconds to human readable format"""
    if not seconds:
        return "0s"
    
    # Convert to timedelta for easier formatting
    td = timedelta(seconds=int(seconds))
    
    # Extract days, hours, minutes, seconds
    days = td.days
    hours = td.seconds // 3600
    minutes = (td.seconds % 3600) // 60
    seconds = td.seconds % 60
    
    # Build the string
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if seconds:
        parts.append(f"{seconds}s")
    
    return " ".join(parts) if parts else "0s"


def get_referrer_source(referrer_url):
    """Extract source from referrer URL"""
    if not referrer_url:
        return "direct"
    
    from urllib.parse import urlparse
    
    try:
        parsed = urlparse(referrer_url)
        domain = parsed.netloc.lower()
        
        # Remove www.
        if domain.startswith("www."):
            domain = domain[4:]
        
        # Map common domains to sources
        source_mapping = {
            "google.": "google",
            "facebook.com": "facebook",
            "twitter.com": "twitter",
            "linkedin.com": "linkedin",
            "instagram.com": "instagram",
            "youtube.com": "youtube",
            "reddit.com": "reddit",
            "pinterest.com": "pinterest",
            "bing.com": "bing",
            "yahoo.com": "yahoo",
            "duckduckgo.com": "duckduckgo",
            "baidu.com": "baidu",
            "yandex.": "yandex"
        }
        
        # Check for matches
        for key, source in source_mapping.items():
            if key in domain:
                return source
        
        # If no match, return the domain
        return domain.split(".")[0] if domain else "referral"
        
    except Exception:
        return "referral"


def get_visitor_from_request():
    """Get or create visitor from current request"""
    # Temporarily return None since Visitor DocType doesn't exist
    return None
    
    # Original implementation commented out:
    # visitor_id = frappe.request.cookies.get('trackflow_visitor')
    # 
    # if visitor_id and frappe.db.exists("Visitor", visitor_id):
    #     return frappe.get_doc("Visitor", visitor_id)
    # 
    # # Create new visitor
    # visitor = frappe.new_doc("Visitor")
    # visitor.visitor_id = frappe.generate_hash(length=32)
    # visitor.first_seen = frappe.utils.now()
    # visitor.last_seen = frappe.utils.now()
    # 
    # # Get visitor info from request
    # if frappe.request:
    #     visitor.ip_address = frappe.request.environ.get('REMOTE_ADDR')
    #     visitor.user_agent = frappe.request.environ.get('HTTP_USER_AGENT')
    #     visitor.referrer = frappe.request.environ.get('HTTP_REFERER')
    #     visitor.landing_page = frappe.request.url
    #     
    #     # Parse user agent
    #     from user_agents import parse
    #     ua = parse(visitor.user_agent)
    #     visitor.browser = ua.browser.family
    #     visitor.browser_version = ua.browser.version_string
    #     visitor.os = ua.os.family
    #     visitor.os_version = ua.os.version_string
    #     visitor.device = ua.device.family
    #     visitor.is_mobile = ua.is_mobile
    #     visitor.is_tablet = ua.is_tablet
    #     visitor.is_bot = ua.is_bot
    # 
    # visitor.insert(ignore_permissions=True)
    # 
    # # Set cookie
    # frappe.local.cookie_manager.set_cookie('trackflow_visitor', visitor.visitor_id)
    # 
    # return visitor


def create_visitor_session(visitor, landing_page=None):
    """Create a new visitor session"""
    # Temporarily return None since Visitor Session DocType doesn't exist
    return None
    
    # Original implementation commented out:
    # session = frappe.new_doc("Visitor Session")
    # session.visitor = visitor.name
    # session.session_id = frappe.generate_hash(length=32)
    # session.start_time = frappe.utils.now()
    # session.last_activity = frappe.utils.now()
    # session.landing_page = landing_page or frappe.request.url if frappe.request else None
    # session.page_views = 1
    # 
    # # Get session info
    # if frappe.request:
    #     session.ip_address = frappe.request.environ.get('REMOTE_ADDR')
    #     session.user_agent = frappe.request.environ.get('HTTP_USER_AGENT')
    #     session.referrer = frappe.request.environ.get('HTTP_REFERER')
    #     
    #     # Get source info
    #     session.source = get_referrer_source(session.referrer)
    #     session.medium = frappe.form_dict.get('utm_medium', 'organic')
    #     session.campaign = frappe.form_dict.get('utm_campaign')
    # 
    # session.insert(ignore_permissions=True)
    # return session


def get_tracking_script(api_key=None):
    """Generate tracking script for website"""
    if not api_key:
        # Try to get default API key
        api_keys = frappe.get_all("TrackFlow API Key", 
                                  filters={"enabled": 1}, 
                                  limit=1, 
                                  fields=["name", "api_key"])
        if api_keys:
            api_key = api_keys[0].api_key
        else:
            return "<!-- TrackFlow: No API key configured -->"
    
    return f"""<!-- TrackFlow Analytics -->
<script>
(function() {{
    var tf = window.trackflow = window.trackflow || [];
    tf.push = function() {{
        tf.queue = tf.queue || [];
        tf.queue.push(arguments);
    }};
    tf.apiKey = '{api_key}';
    tf.visitor = getCookie('trackflow_visitor');
    
    function getCookie(name) {{
        var value = "; " + document.cookie;
        var parts = value.split("; " + name + "=");
        if (parts.length == 2) return parts.pop().split(";").shift();
    }}
    
    // Track page view
    tf.push('track', 'pageview', {{
        url: window.location.href,
        title: document.title,
        referrer: document.referrer
    }});
    
    // Load tracking script
    var script = document.createElement('script');
    script.async = true;
    script.src = '/assets/trackflow/js/trackflow-web.js';
    document.head.appendChild(script);
}})();
</script>
<!-- End TrackFlow Analytics -->"""


def calculate_attribution_credit(touchpoints, model="last_touch"):
    """Calculate attribution credit for touchpoints based on model"""
    if not touchpoints:
        return []
    
    total_touchpoints = len(touchpoints)
    
    if model == "last_touch":
        # 100% credit to last touchpoint
        for i, tp in enumerate(touchpoints):
            tp["credit"] = 100 if i == total_touchpoints - 1 else 0
            
    elif model == "first_touch":
        # 100% credit to first touchpoint
        for i, tp in enumerate(touchpoints):
            tp["credit"] = 100 if i == 0 else 0
            
    elif model == "linear":
        # Equal credit to all touchpoints
        credit = 100 / total_touchpoints
        for tp in touchpoints:
            tp["credit"] = credit
            
    elif model == "time_decay":
        # More credit to recent touchpoints
        half_life_days = 7
        current_time = frappe.utils.now_datetime()
        
        # Calculate decay scores
        scores = []
        for tp in touchpoints:
            tp_time = frappe.utils.get_datetime(tp.get("timestamp"))
            days_ago = (current_time - tp_time).days
            score = 0.5 ** (days_ago / half_life_days)
            scores.append(score)
        
        # Normalize to 100%
        total_score = sum(scores)
        for i, tp in enumerate(touchpoints):
            tp["credit"] = (scores[i] / total_score) * 100 if total_score > 0 else 0
            
    elif model == "position_based":
        # 40% first, 40% last, 20% middle
        if total_touchpoints == 1:
            touchpoints[0]["credit"] = 100
        elif total_touchpoints == 2:
            touchpoints[0]["credit"] = 50
            touchpoints[1]["credit"] = 50
        else:
            middle_credit = 20 / (total_touchpoints - 2)
            for i, tp in enumerate(touchpoints):
                if i == 0:
                    tp["credit"] = 40
                elif i == total_touchpoints - 1:
                    tp["credit"] = 40
                else:
                    tp["credit"] = middle_credit
    
    return touchpoints
