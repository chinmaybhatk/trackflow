import frappe
from frappe import _
import json

@frappe.whitelist(allow_guest=True)
def track_event():
    """Track custom events from frontend"""
    try:
        data = json.loads(frappe.request.data)
        
        # Get or create visitor
        visitor_id = data.get("visitor_id") or frappe.request.cookies.get("tf_visitor_id")
        
        if not visitor_id:
            import uuid
            visitor_id = str(uuid.uuid4())
            
        # Create event record
        event = frappe.new_doc("Click Event")
        event.visitor_id = visitor_id
        event.event_type = data.get("event_type", "pageview")
        event.event_data = json.dumps(data.get("properties", {}))
        event.page_url = data.get("url")
        event.referrer = data.get("referrer")
        event.ip_address = frappe.local.request_ip
        event.user_agent = frappe.request.headers.get("User-Agent", "")
        
        # UTM parameters
        event.utm_source = data.get("utm_source")
        event.utm_medium = data.get("utm_medium")
        event.utm_campaign = data.get("utm_campaign")
        event.utm_term = data.get("utm_term")
        event.utm_content = data.get("utm_content")
        
        event.insert(ignore_permissions=True)
        frappe.db.commit()
        
        return {"status": "success", "visitor_id": visitor_id}
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "TrackFlow Event Tracking Error")
        return {"status": "error", "message": str(e)}

@frappe.whitelist(allow_guest=True)
def get_tracking_script():
    """Get tracking JavaScript code"""
    try:
        settings = frappe.get_single("TrackFlow Settings")
        
        script = f"""
<!-- TrackFlow Tracking Code -->
<script>
(function() {{
    var tf = window.trackflow = window.trackflow || [];
    tf.site_url = '{frappe.utils.get_url()}';
    tf.visitor_id = localStorage.getItem('tf_visitor_id');
    
    // Track pageview
    tf.track = function(event, properties) {{
        var data = {{
            event_type: event || 'pageview',
            visitor_id: tf.visitor_id,
            url: window.location.href,
            referrer: document.referrer,
            properties: properties || {{}},
            timestamp: new Date().toISOString()
        }};
        
        // Get UTM parameters
        var urlParams = new URLSearchParams(window.location.search);
        data.utm_source = urlParams.get('utm_source');
        data.utm_medium = urlParams.get('utm_medium');
        data.utm_campaign = urlParams.get('utm_campaign');
        data.utm_term = urlParams.get('utm_term');
        data.utm_content = urlParams.get('utm_content');
        
        // Send tracking data
        fetch(tf.site_url + '/api/method/trackflow.api.tracking.track_event', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify(data),
            credentials: 'include'
        }}).then(function(response) {{
            return response.json();
        }}).then(function(result) {{
            if (result.visitor_id && !tf.visitor_id) {{
                tf.visitor_id = result.visitor_id;
                localStorage.setItem('tf_visitor_id', tf.visitor_id);
            }}
        }});
    }};
    
    // Auto-track pageview
    tf.track('pageview');
    
    // Track clicks on tracked links
    document.addEventListener('click', function(e) {{
        var link = e.target.closest('a');
        if (link && link.href && link.href.includes('/r/')) {{
            tf.track('link_click', {{
                url: link.href,
                text: link.innerText
            }});
        }}
    }});
}})();
</script>
<!-- End TrackFlow Tracking Code -->
"""
        
        return script
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "TrackFlow Script Generation Error")
        return "<!-- TrackFlow Error: Could not generate tracking script -->"

@frappe.whitelist()
def create_tracked_link(target_url, campaign=None, source=None, medium=None, term=None, content=None):
    """Create a new tracked link"""
    try:
        # Validate URL
        if not target_url:
            frappe.throw(_("Target URL is required"))
            
        # Build URL with UTM parameters
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        
        parsed = urlparse(target_url)
        params = parse_qs(parsed.query)
        
        # Add UTM parameters
        if campaign:
            params['utm_campaign'] = [campaign]
        if source:
            params['utm_source'] = [source]
        if medium:
            params['utm_medium'] = [medium]
        if term:
            params['utm_term'] = [term]
        if content:
            params['utm_content'] = [content]
            
        # Rebuild URL
        query = urlencode(params, doseq=True)
        final_url = urlunparse(parsed._replace(query=query))
        
        # Create tracked link
        link = frappe.new_doc("Tracked Link")
        link.target_url = final_url
        link.campaign = campaign
        link.source = source
        link.medium = medium
        link.is_active = 1
        link.insert()
        
        # Generate short URL
        short_url = f"{frappe.utils.get_url()}/r/{link.short_code}"
        
        return {
            "status": "success",
            "short_url": short_url,
            "tracking_id": link.short_code,
            "name": link.name
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "TrackFlow Create Link Error")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_link_stats(tracking_id):
    """Get statistics for a tracked link"""
    try:
        link = frappe.get_doc("Tracked Link", {"short_code": tracking_id})
        
        # Get click data
        clicks = frappe.db.sql("""
            SELECT 
                COUNT(*) as total_clicks,
                COUNT(DISTINCT visitor_id) as unique_visitors,
                COUNT(DISTINCT DATE(creation)) as days_active,
                MIN(creation) as first_click,
                MAX(creation) as last_click
            FROM `tabClick Event`
            WHERE tracked_link = %s
        """, link.name, as_dict=True)[0]
        
        # Get conversion data
        conversions = frappe.db.count("Link Conversion", {"tracked_link": link.name})
        
        # Get geographic data
        geo_data = frappe.db.sql("""
            SELECT 
                country,
                COUNT(*) as clicks
            FROM `tabClick Event`
            WHERE tracked_link = %s
            GROUP BY country
            ORDER BY clicks DESC
            LIMIT 10
        """, link.name, as_dict=True)
        
        return {
            "link_info": {
                "short_code": link.short_code,
                "target_url": link.target_url,
                "created": str(link.creation),
                "is_active": link.is_active
            },
            "stats": {
                "total_clicks": clicks.total_clicks or 0,
                "unique_visitors": clicks.unique_visitors or 0,
                "conversions": conversions,
                "conversion_rate": (conversions / clicks.total_clicks * 100) if clicks.total_clicks else 0,
                "first_click": str(clicks.first_click) if clicks.first_click else None,
                "last_click": str(clicks.last_click) if clicks.last_click else None
            },
            "geography": geo_data
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "TrackFlow Get Stats Error")
        return {"status": "error", "message": str(e)}
