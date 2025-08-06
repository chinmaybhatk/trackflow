import frappe
from frappe import _

def inject_tracking_script(doc, method):
    """
    Inject TrackFlow tracking script into web forms
    """
    if not doc.trackflow_tracking_enabled:
        return
        
    # Get tracking script
    tracking_script = get_tracking_script()
    
    # Add to web form scripts
    if tracking_script:
        if not doc.client_script:
            doc.client_script = ""
        
        # Check if script already exists
        if "trackflow" not in doc.client_script:
            doc.client_script += f"\n\n{tracking_script}"
    
def validate_tracking_settings(doc, method):
    """
    Validate tracking settings for web form
    """
    if doc.trackflow_tracking_enabled and not doc.trackflow_conversion_goal:
        frappe.throw(_("Please set a conversion goal for tracking"))

def on_web_form_submit(doc, method):
    """
    Track web form submissions
    """
    # Check if this is a web form submission
    if not frappe.local.request or not frappe.local.request.url:
        return
        
    # Check if tracking is enabled
    web_form_name = frappe.local.form_dict.get("web_form")
    if not web_form_name:
        return
        
    try:
        web_form = frappe.get_doc("Web Form", web_form_name)
        if not web_form.trackflow_tracking_enabled:
            return
            
        # Get visitor ID from cookies
        visitor_id = frappe.local.request.cookies.get("trackflow_visitor_id")
        if not visitor_id:
            return
            
        # Track conversion
        from trackflow.tracking import track_conversion
        track_conversion(
            visitor_id=visitor_id,
            conversion_type="web_form",
            conversion_value=web_form.trackflow_conversion_goal,
            metadata={
                "web_form": web_form_name,
                "doctype": doc.doctype,
                "doc_name": doc.name
            }
        )
        
        # Update visitor profile
        from trackflow.utils import update_visitor_profile
        update_visitor_profile(visitor_id, {
            "last_conversion": frappe.utils.now(),
            "conversion_count": frappe.db.sql("""
                SELECT COUNT(*) FROM `tabConversion`
                WHERE visitor_id = %s
            """, visitor_id)[0][0]
        })
        
    except Exception as e:
        frappe.log_error(f"TrackFlow web form tracking error: {str(e)}")

def get_tracking_script():
    """
    Get the tracking script to inject into web forms
    """
    try:
        settings = frappe.get_single("TrackFlow Settings")
        if not settings.enabled:
            return ""
            
        site_url = frappe.utils.get_url()
        
        script = f"""
        <!-- TrackFlow Tracking Script -->
        <script>
        (function() {{
            // Initialize TrackFlow
            window.TrackFlow = window.TrackFlow || [];
            
            // Get or create visitor ID
            function getVisitorId() {{
                var visitorId = getCookie('trackflow_visitor_id');
                if (!visitorId) {{
                    visitorId = generateVisitorId();
                    setCookie('trackflow_visitor_id', visitorId, 365);
                }}
                return visitorId;
            }}
            
            // Generate unique visitor ID
            function generateVisitorId() {{
                return 'tf_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            }}
            
            // Cookie helpers
            function getCookie(name) {{
                var value = "; " + document.cookie;
                var parts = value.split("; " + name + "=");
                if (parts.length == 2) return parts.pop().split(";").shift();
            }}
            
            function setCookie(name, value, days) {{
                var expires = "";
                if (days) {{
                    var date = new Date();
                    date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
                    expires = "; expires=" + date.toUTCString();
                }}
                document.cookie = name + "=" + (value || "") + expires + "; path=/";
            }}
            
            // Track page view
            function trackPageView() {{
                var data = {{
                    visitor_id: getVisitorId(),
                    url: window.location.href,
                    referrer: document.referrer,
                    timestamp: new Date().toISOString(),
                    source: getQueryParam('utm_source'),
                    medium: getQueryParam('utm_medium'),
                    campaign: getQueryParam('utm_campaign'),
                    user_agent: navigator.userAgent
                }};
                
                // Send tracking data
                fetch('{site_url}/api/method/trackflow.api.tracking.track_event', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                        'X-Frappe-CSRF-Token': frappe.csrf_token
                    }},
                    body: JSON.stringify({{
                        event_type: 'page_view',
                        data: data
                    }})
                }});
            }}
            
            // Get query parameter
            function getQueryParam(param) {{
                var urlParams = new URLSearchParams(window.location.search);
                return urlParams.get(param);
            }}
            
            // Track form submission
            if (window.frappe && window.frappe.web_form) {{
                frappe.web_form.events.on('after_save', function() {{
                    var data = {{
                        visitor_id: getVisitorId(),
                        form_name: frappe.web_form.web_form_name,
                        timestamp: new Date().toISOString()
                    }};
                    
                    fetch('{site_url}/api/method/trackflow.api.tracking.track_event', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                            'X-Frappe-CSRF-Token': frappe.csrf_token
                        }},
                        body: JSON.stringify({{
                            event_type: 'form_submission',
                            data: data
                        }})
                    }});
                }});
            }}
            
            // Initialize tracking
            trackPageView();
        }})();
        </script>
        """
        
        return script
        
    except Exception as e:
        frappe.log_error(f"Error generating tracking script: {str(e)}")
        return ""
