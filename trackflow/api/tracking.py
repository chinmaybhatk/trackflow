"""
Tracking API endpoints
"""

import frappe
from frappe import _
import json


@frappe.whitelist(allow_guest=True)
def get_tracking_script():
    """Return the tracking JavaScript"""
    settings = frappe.get_single("TrackFlow Settings") if frappe.db.exists("DocType", "TrackFlow Settings") else None
    
    if not settings or not settings.enable_tracking:
        return ""
    
    tracking_domain = settings.tracking_domain or frappe.utils.get_url()
    
    script = f"""
(function() {{
    // TrackFlow Analytics Script
    var TrackFlow = window.TrackFlow || {{}};
    
    TrackFlow.init = function() {{
        // Get or create visitor ID
        var visitorId = TrackFlow.getCookie('trackflow_visitor');
        if (!visitorId) {{
            visitorId = 'v_' + Math.random().toString(36).substr(2, 16);
            TrackFlow.setCookie('trackflow_visitor', visitorId, 365);
        }}
        
        // Get session ID
        var sessionId = TrackFlow.getCookie('trackflow_session');
        if (!sessionId) {{
            sessionId = 's_' + Math.random().toString(36).substr(2, 16);
            TrackFlow.setCookie('trackflow_session', sessionId, 0.5); // 30 minutes
        }}
        
        // Track page view
        TrackFlow.track('pageview', {{
            url: window.location.href,
            title: document.title,
            referrer: document.referrer,
            visitor: visitorId,
            session: sessionId
        }});
    }};
    
    TrackFlow.track = function(event, data) {{
        data = data || {{}};
        data.event = event;
        data.timestamp = new Date().toISOString();
        
        // Get UTM parameters
        var params = new URLSearchParams(window.location.search);
        data.utm_source = params.get('utm_source');
        data.utm_medium = params.get('utm_medium');
        data.utm_campaign = params.get('utm_campaign');
        data.utm_term = params.get('utm_term');
        data.utm_content = params.get('utm_content');
        
        // Send tracking data
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '{tracking_domain}/api/method/trackflow.api.tracking.track_event', true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.send(JSON.stringify(data));
    }};
    
    TrackFlow.getCookie = function(name) {{
        var value = "; " + document.cookie;
        var parts = value.split("; " + name + "=");
        if (parts.length == 2) return parts.pop().split(";").shift();
    }};
    
    TrackFlow.setCookie = function(name, value, days) {{
        var expires = "";
        if (days) {{
            var date = new Date();
            date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
            expires = "; expires=" + date.toUTCString();
        }}
        document.cookie = name + "=" + value + expires + "; path=/";
    }};
    
    // Initialize on load
    if (document.readyState === "loading") {{
        document.addEventListener("DOMContentLoaded", TrackFlow.init);
    }} else {{
        TrackFlow.init();
    }}
    
    window.TrackFlow = TrackFlow;
}})();
"""
    
    # Return as JavaScript response
    frappe.response["content_type"] = "application/javascript"
    return script


@frappe.whitelist(allow_guest=True)
def track_event():
    """Track an event from the client"""
    try:
        data = json.loads(frappe.request.data) if frappe.request.data else {}
        
        # Get visitor ID
        visitor_id = data.get("visitor")
        if not visitor_id:
            return {"status": "error", "message": "Visitor ID required"}
            
        # Get or create visitor
        if frappe.db.exists("Visitor", visitor_id):
            visitor = frappe.get_doc("Visitor", visitor_id)
        else:
            visitor = frappe.new_doc("Visitor")
            visitor.visitor_id = visitor_id
            visitor.first_seen = frappe.utils.now()
            
        # Update visitor info
        visitor.last_seen = frappe.utils.now()
        visitor.ip_address = frappe.local.request_ip
        visitor.user_agent = frappe.request.headers.get('User-Agent', '')
        
        # Update UTM parameters if provided
        if data.get("utm_source"):
            visitor.source = data.get("utm_source")
        if data.get("utm_medium"):
            visitor.medium = data.get("utm_medium")
        if data.get("utm_campaign"):
            visitor.campaign = data.get("utm_campaign")
            
        visitor.save(ignore_permissions=True)
        
        # Create event
        event_type = data.get("event", "pageview")
        if event_type == "pageview":
            create_pageview_event(visitor, data)
        elif event_type == "form_submit":
            create_form_submit_event(visitor, data)
        else:
            create_custom_event(visitor, data)
            
        return {"status": "success"}
        
    except Exception as e:
        frappe.log_error(f"Error tracking event: {str(e)}")
        return {"status": "error", "message": str(e)}


def create_pageview_event(visitor, data):
    """Create a page view event"""
    event = frappe.new_doc("Visitor Event")
    event.visitor = visitor.name
    event.event_type = "page_view"
    event.event_category = "navigation"
    event.url = data.get("url", "")
    event.event_data = json.dumps({
        "title": data.get("title", ""),
        "referrer": data.get("referrer", ""),
        "session": data.get("session", "")
    })
    event.timestamp = frappe.utils.now()
    event.insert(ignore_permissions=True)


def create_form_submit_event(visitor, data):
    """Create a form submission event"""
    event = frappe.new_doc("Visitor Event")
    event.visitor = visitor.name
    event.event_type = "form_submission"
    event.event_category = "engagement"
    event.url = data.get("url", "")
    event.event_data = json.dumps({
        "form_id": data.get("form_id", ""),
        "form_name": data.get("form_name", ""),
        "fields": data.get("fields", {})
    })
    event.timestamp = frappe.utils.now()
    event.insert(ignore_permissions=True)


def create_custom_event(visitor, data):
    """Create a custom event"""
    event = frappe.new_doc("Visitor Event")
    event.visitor = visitor.name
    event.event_type = data.get("event", "custom")
    event.event_category = data.get("category", "custom")
    event.url = data.get("url", "")
    event.event_data = json.dumps(data)
    event.timestamp = frappe.utils.now()
    event.insert(ignore_permissions=True)
