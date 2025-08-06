"""
Jinja methods for TrackFlow templates
"""

import frappe
from frappe import _
from trackflow.utils import format_duration, get_referrer_source


def get_tracking_pixel_url(visitor_id):
    """Get tracking pixel URL for a visitor"""
    return f"/trackflow/pixel/{visitor_id}"


def get_redirect_url(tracking_link_id):
    """Get redirect URL for a tracking link"""
    return f"/r/{tracking_link_id}"


def format_campaign_metrics(campaign):
    """Format campaign metrics for display"""
    if not campaign:
        return {}
        
    return {
        "clicks": campaign.get("total_clicks", 0),
        "conversions": campaign.get("conversions", 0),
        "conversion_rate": f"{campaign.get('conversion_rate', 0):.2f}%",
        "cost_per_click": f"${campaign.get('cost_per_click', 0):.2f}",
        "roi": f"{campaign.get('roi', 0):.2f}%"
    }


def get_visitor_avatar(visitor):
    """Get visitor avatar or initials"""
    if visitor.get("email"):
        # Use gravatar if email available
        import hashlib
        email_hash = hashlib.md5(visitor.email.lower().encode()).hexdigest()
        return f"https://www.gravatar.com/avatar/{email_hash}?d=mp"
    else:
        # Return initials
        return None


def get_source_icon(source):
    """Get icon for traffic source"""
    icons = {
        "google": "fa fa-google",
        "facebook": "fa fa-facebook",
        "twitter": "fa fa-twitter",
        "linkedin": "fa fa-linkedin",
        "email": "fa fa-envelope",
        "direct": "fa fa-link",
        "referral": "fa fa-external-link"
    }
    
    return icons.get(source, "fa fa-globe")


def get_device_icon(device_type):
    """Get icon for device type"""
    icons = {
        "desktop": "fa fa-desktop",
        "mobile": "fa fa-mobile",
        "tablet": "fa fa-tablet"
    }
    
    return icons.get(device_type, "fa fa-desktop")


def format_visitor_location(visitor):
    """Format visitor location for display"""
    parts = []
    
    if visitor.get("city"):
        parts.append(visitor.city)
    if visitor.get("region"):
        parts.append(visitor.region)
    if visitor.get("country"):
        parts.append(visitor.country)
        
    return ", ".join(parts) if parts else "Unknown"


def get_campaign_status_badge(campaign):
    """Get status badge HTML for campaign"""
    status = campaign.get("status", "draft")
    
    badges = {
        "active": '<span class="badge badge-success">Active</span>',
        "paused": '<span class="badge badge-warning">Paused</span>',
        "completed": '<span class="badge badge-info">Completed</span>',
        "draft": '<span class="badge badge-secondary">Draft</span>'
    }
    
    return badges.get(status, '<span class="badge badge-secondary">Unknown</span>')


def get_attribution_model_description(model):
    """Get description for attribution model"""
    descriptions = {
        "last_touch": "Assigns 100% credit to the last touchpoint",
        "first_touch": "Assigns 100% credit to the first touchpoint",
        "linear": "Distributes credit equally across all touchpoints",
        "time_decay": "Gives more credit to recent touchpoints",
        "position_based": "40% to first, 40% to last, 20% to middle touchpoints"
    }
    
    return descriptions.get(model, "Custom attribution model")


def format_touchpoint_timeline(touchpoints):
    """Format touchpoints for timeline display"""
    if not touchpoints:
        return []
        
    formatted = []
    for tp in touchpoints:
        formatted.append({
            "timestamp": frappe.utils.format_datetime(tp.get("timestamp")),
            "source": tp.get("source", "direct"),
            "icon": get_source_icon(tp.get("source", "direct")),
            "description": f"{tp.get('type', 'pageview')} from {tp.get('source', 'direct')}",
            "credit": f"{tp.get('credit', 0)}%" if tp.get('credit') else None
        })
        
    return formatted


def get_conversion_funnel_data(campaign):
    """Get funnel visualization data"""
    return {
        "stages": [
            {"name": "Visits", "value": campaign.get("total_clicks", 0)},
            {"name": "Engaged", "value": campaign.get("engaged_visitors", 0)},
            {"name": "Leads", "value": campaign.get("leads_generated", 0)},
            {"name": "Customers", "value": campaign.get("customers_acquired", 0)}
        ]
    }


def format_currency(amount, currency="USD"):
    """Format currency for display"""
    if currency == "USD":
        return f"${amount:,.2f}"
    else:
        return f"{currency} {amount:,.2f}"


def get_tracking_script_tag():
    """Get complete tracking script tag for website"""
    return """<!-- TrackFlow Analytics -->
<script>
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
</script>
<!-- End TrackFlow Analytics -->"""
