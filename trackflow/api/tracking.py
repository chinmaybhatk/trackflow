import frappe
from frappe import _
import json
from datetime import datetime

@frappe.whitelist(allow_guest=True)
def track_event():
    """Track custom events via API."""
    try:
        data = json.loads(frappe.request.data)
        
        # Validate required fields
        if not data.get("visitor_id"):
            frappe.throw(_("Visitor ID is required"))
        
        if not data.get("event_type"):
            frappe.throw(_("Event type is required"))
        
        # Get visitor
        visitor = frappe.db.get_value("Visitor", {"visitor_id": data.get("visitor_id")}, "name")
        if not visitor:
            frappe.throw(_("Invalid visitor ID"))
        
        # Get or create session
        session = get_active_session(visitor)
        
        # Record custom event
        event = frappe.get_doc({
            "doctype": "Custom Event",
            "visitor": visitor,
            "session": session,
            "event_type": data.get("event_type"),
            "event_category": data.get("category"),
            "event_action": data.get("action"),
            "event_label": data.get("label"),
            "event_value": data.get("value"),
            "timestamp": datetime.now(),
            "properties": json.dumps(data.get("properties", {}))
        })
        event.insert(ignore_permissions=True)
        
        return {
            "success": True,
            "event_id": event.name
        }
        
    except Exception as e:
        frappe.log_error(f"Track event error: {str(e)}", "TrackFlow API")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist(allow_guest=True)
def track_conversion():
    """Track conversion event."""
    try:
        data = json.loads(frappe.request.data)
        
        # Validate required fields
        if not data.get("visitor_id"):
            frappe.throw(_("Visitor ID is required"))
        
        if not data.get("conversion_type"):
            frappe.throw(_("Conversion type is required"))
        
        # Get visitor
        visitor = frappe.db.get_value("Visitor", {"visitor_id": data.get("visitor_id")}, "name")
        if not visitor:
            frappe.throw(_("Invalid visitor ID"))
        
        # Create conversion record
        conversion = frappe.get_doc({
            "doctype": "Conversion",
            "visitor": visitor,
            "conversion_type": data.get("conversion_type"),
            "conversion_value": data.get("value", 0),
            "currency": data.get("currency", frappe.db.get_default("currency")),
            "timestamp": datetime.now(),
            "source": data.get("source"),
            "medium": data.get("medium"),
            "campaign": data.get("campaign"),
            "metadata": json.dumps(data.get("metadata", {}))
        })
        conversion.insert(ignore_permissions=True)
        
        # Update visitor conversion status
        frappe.db.set_value("Visitor", visitor, {
            "has_converted": 1,
            "conversion_date": datetime.now(),
            "total_conversion_value": frappe.db.sql("""
                SELECT SUM(conversion_value) 
                FROM `tabConversion` 
                WHERE visitor = %s
            """, visitor)[0][0] or 0
        })
        
        # Trigger attribution calculation if configured
        if data.get("calculate_attribution"):
            calculate_conversion_attribution(conversion)
        
        return {
            "success": True,
            "conversion_id": conversion.name
        }
        
    except Exception as e:
        frappe.log_error(f"Track conversion error: {str(e)}", "TrackFlow API")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist(allow_guest=True)
def track_pageview():
    """Track page view event."""
    try:
        data = json.loads(frappe.request.data)
        
        # Validate required fields
        if not data.get("visitor_id"):
            frappe.throw(_("Visitor ID is required"))
        
        if not data.get("page_url"):
            frappe.throw(_("Page URL is required"))
        
        # Get visitor
        visitor = frappe.db.get_value("Visitor", {"visitor_id": data.get("visitor_id")}, "name")
        if not visitor:
            # Create new visitor
            visitor_doc = frappe.get_doc({
                "doctype": "Visitor",
                "visitor_id": data.get("visitor_id"),
                "first_seen": datetime.now(),
                "last_seen": datetime.now(),
                "first_referrer": data.get("referrer", ""),
                "first_landing_page": data.get("page_url")
            })
            visitor_doc.insert(ignore_permissions=True)
            visitor = visitor_doc.name
        
        # Get or create session
        session = get_active_session(visitor)
        
        # Record page view
        page_view = frappe.get_doc({
            "doctype": "Page View",
            "visitor": visitor,
            "session": session,
            "page_url": data.get("page_url"),
            "page_title": data.get("page_title", ""),
            "referrer": data.get("referrer", ""),
            "timestamp": datetime.now(),
            "time_on_page": 0
        })
        page_view.insert(ignore_permissions=True)
        
        # Update session activity
        frappe.db.set_value("Visitor Session", session, {
            "last_activity": datetime.now(),
            "page_count": frappe.db.sql("""
                SELECT COUNT(*) FROM `tabPage View` WHERE session = %s
            """, session)[0][0]
        })
        
        return {
            "success": True,
            "pageview_id": page_view.name,
            "session_id": session
        }
        
    except Exception as e:
        frappe.log_error(f"Track pageview error: {str(e)}", "TrackFlow API")
        return {
            "success": False,
            "error": str(e)
        }

def get_active_session(visitor):
    """Get or create active session for visitor."""
    # Check for active session (within last 30 minutes)
    active_session = frappe.db.get_value(
        "Visitor Session",
        {
            "visitor": visitor,
            "start_time": [">=", frappe.utils.add_to_date(datetime.now(), minutes=-30)]
        },
        "name"
    )
    
    if active_session:
        return active_session
    
    # Create new session
    session = frappe.get_doc({
        "doctype": "Visitor Session",
        "visitor": visitor,
        "session_id": frappe.generate_hash()[:16],
        "start_time": datetime.now(),
        "last_activity": datetime.now(),
        "page_count": 0,
        "duration": 0
    })
    session.insert(ignore_permissions=True)
    
    return session.name

def calculate_conversion_attribution(conversion):
    """Calculate attribution for a conversion."""
    # Get all touchpoints for the visitor
    touchpoints = frappe.db.sql("""
        SELECT 
            pv.timestamp,
            tl.utm_source as source,
            tl.utm_medium as medium,
            tl.utm_campaign as campaign,
            tl.name as tracking_link
        FROM `tabPage View` pv
        LEFT JOIN `tabTracking Link` tl ON tl.name = pv.tracking_link
        WHERE pv.visitor = %s
        ORDER BY pv.timestamp
    """, conversion.visitor, as_dict=True)
    
    if not touchpoints:
        return
    
    # Get active attribution models
    models = frappe.get_all(
        "Attribution Model",
        filters={"is_active": 1},
        fields=["name", "model_type"]
    )
    
    for model in models:
        apply_attribution_model(conversion, touchpoints, model)

def apply_attribution_model(conversion, touchpoints, model):
    """Apply specific attribution model to conversion."""
    # This is a simplified implementation
    # Real implementation would be more complex
    
    if model.model_type == "First Touch":
        # 100% credit to first touchpoint
        if touchpoints:
            create_attribution_record(
                conversion, touchpoints[0], model.name, 100
            )
    
    elif model.model_type == "Last Touch":
        # 100% credit to last touchpoint
        if touchpoints:
            create_attribution_record(
                conversion, touchpoints[-1], model.name, 100
            )
    
    elif model.model_type == "Linear":
        # Equal credit to all touchpoints
        weight = 100.0 / len(touchpoints) if touchpoints else 0
        for touchpoint in touchpoints:
            create_attribution_record(
                conversion, touchpoint, model.name, weight
            )

def create_attribution_record(conversion, touchpoint, model, weight):
    """Create attribution record."""
    # Implementation would create Deal Attribution records
    # This is simplified for the example
    pass

@frappe.whitelist()
def get_tracking_script(api_key):
    """Get tracking script for website integration."""
    if not frappe.db.exists("TrackFlow API Key", {"api_key": api_key, "is_active": 1}):
        frappe.throw(_("Invalid or inactive API key"))
    
    site_url = frappe.utils.get_url()
    
    script = f"""
<!-- TrackFlow Tracking Script -->
<script>
(function() {{
    var tf = window.trackflow = window.trackflow || [];
    tf.apiKey = '{api_key}';
    tf.apiUrl = '{site_url}/api/method/trackflow.api.tracking.';
    
    // Get or create visitor ID
    function getVisitorId() {{
        var visitorId = localStorage.getItem('tf_visitor_id');
        if (!visitorId) {{
            visitorId = 'tf_' + Math.random().toString(36).substr(2, 9) + Date.now().toString(36);
            localStorage.setItem('tf_visitor_id', visitorId);
        }}
        return visitorId;
    }}
    
    tf.visitorId = getVisitorId();
    
    // Track page view
    tf.trackPageView = function(data) {{
        data = data || {{}};
        data.visitor_id = tf.visitorId;
        data.page_url = window.location.href;
        data.page_title = document.title;
        data.referrer = document.referrer;
        
        fetch(tf.apiUrl + 'track_pageview', {{
            method: 'POST',
            headers: {{
                'Content-Type': 'application/json',
                'X-Frappe-API-Key': tf.apiKey
            }},
            body: JSON.stringify(data)
        }});
    }};
    
    // Track custom event
    tf.trackEvent = function(eventType, data) {{
        data = data || {{}};
        data.visitor_id = tf.visitorId;
        data.event_type = eventType;
        
        fetch(tf.apiUrl + 'track_event', {{
            method: 'POST',
            headers: {{
                'Content-Type': 'application/json',
                'X-Frappe-API-Key': tf.apiKey
            }},
            body: JSON.stringify(data)
        }});
    }};
    
    // Track conversion
    tf.trackConversion = function(conversionType, value, data) {{
        data = data || {{}};
        data.visitor_id = tf.visitorId;
        data.conversion_type = conversionType;
        data.value = value;
        
        fetch(tf.apiUrl + 'track_conversion', {{
            method: 'POST',
            headers: {{
                'Content-Type': 'application/json',
                'X-Frappe-API-Key': tf.apiKey
            }},
            body: JSON.stringify(data)
        }});
    }};
    
    // Auto-track page views
    tf.trackPageView();
    
    // Track page unload time
    window.addEventListener('beforeunload', function() {{
        // Send timing data
        var timeOnPage = Math.round((Date.now() - performance.timing.navigationStart) / 1000);
        tf.trackEvent('page_unload', {{
            time_on_page: timeOnPage,
            page_url: window.location.href
        }});
    }});
}})();
</script>
<!-- End TrackFlow Tracking Script -->
"""
    
    return script
