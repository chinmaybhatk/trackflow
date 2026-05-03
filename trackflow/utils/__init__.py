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

    td = timedelta(seconds=int(seconds))

    days = td.days
    hours = td.seconds // 3600
    minutes = (td.seconds % 3600) // 60
    secs = td.seconds % 60

    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if secs:
        parts.append(f"{secs}s")

    return " ".join(parts) if parts else "0s"


def get_referrer_source(referrer_url):
    """Extract source from referrer URL"""
    if not referrer_url:
        return "direct"

    from urllib.parse import urlparse

    try:
        parsed = urlparse(referrer_url)
        domain = parsed.netloc.lower()

        if domain.startswith("www."):
            domain = domain[4:]

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
            "yandex.": "yandex",
        }

        for key, source in source_mapping.items():
            if key in domain:
                return source

        return domain.split(".")[0] if domain else "referral"

    except Exception:
        return "referral"


def get_visitor_from_request():
    """Get or create visitor from current request"""
    from trackflow.trackflow.utils import get_visitor_from_request as _get_visitor
    try:
        return _get_visitor()
    except Exception:
        return None


def create_visitor_session(visitor, landing_page=None):
    """Create a new visitor session"""
    try:
        session = frappe.new_doc("Visitor Session")
        session.visitor = visitor.name if hasattr(visitor, "name") else visitor
        session.session_id = frappe.generate_hash(length=32)
        session.start_time = frappe.utils.now()
        session.last_activity = frappe.utils.now()
        session.landing_page = landing_page
        session.page_views = 1

        if frappe.request:
            session.ip_address = frappe.request.environ.get("REMOTE_ADDR")
            session.user_agent = frappe.request.environ.get("HTTP_USER_AGENT")
            session.referrer = frappe.request.environ.get("HTTP_REFERER")
            session.source = get_referrer_source(session.referrer)
            session.medium = frappe.form_dict.get("utm_medium", "organic")
            session.campaign = frappe.form_dict.get("utm_campaign")

        session.insert(ignore_permissions=True)
        return session

    except Exception as e:
        frappe.log_error(f"Error creating visitor session: {str(e)}", "TrackFlow")
        return None


def get_tracking_script(api_key=None):
    """Generate tracking script for website"""
    if not api_key:
        api_keys = frappe.get_all(
            "TrackFlow API Key",
            filters={"enabled": 1},
            limit=1,
            fields=["name", "api_key"],
        )
        if api_keys:
            api_key = api_keys[0].api_key
        else:
            return "<!-- TrackFlow: No API key configured -->"

    site_url = frappe.utils.get_url()
    return f"""<!-- TrackFlow Analytics -->
<script>
(function() {{
    var tf = window.trackflow = window.trackflow || [];
    tf.push = function() {{
        tf.queue = tf.queue || [];
        tf.queue.push(arguments);
    }};
    tf.apiKey = '{api_key}';
    tf.endpoint = '{site_url}';

    tf.push('track', 'pageview', {{
        url: window.location.href,
        title: document.title,
        referrer: document.referrer
    }});

    var script = document.createElement('script');
    script.async = true;
    script.src = '{site_url}/assets/trackflow/js/trackflow-web.js';
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
        for i, tp in enumerate(touchpoints):
            tp["credit"] = 100 if i == total_touchpoints - 1 else 0

    elif model == "first_touch":
        for i, tp in enumerate(touchpoints):
            tp["credit"] = 100 if i == 0 else 0

    elif model == "linear":
        credit = 100 / total_touchpoints
        for tp in touchpoints:
            tp["credit"] = credit

    elif model == "time_decay":
        half_life_days = 7
        current_time = frappe.utils.now_datetime()

        scores = []
        for tp in touchpoints:
            tp_time = frappe.utils.get_datetime(tp.get("timestamp"))
            days_ago = (current_time - tp_time).days
            score = 0.5 ** (days_ago / half_life_days)
            scores.append(score)

        total_score = sum(scores)
        for i, tp in enumerate(touchpoints):
            tp["credit"] = (scores[i] / total_score) * 100 if total_score > 0 else 0

    elif model == "position_based":
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
