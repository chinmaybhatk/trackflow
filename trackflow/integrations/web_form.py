"""
Web Form Integration for TrackFlow
"""

import frappe
from frappe import _


def inject_tracking_script(doc, method):
    """Inject tracking script into web forms"""
    # Skip if tracking is not enabled for this form
    if not doc.get("trackflow_tracking_enabled"):
        return
        
    # Add tracking script to form
    tracking_script = get_web_form_tracking_script(doc)
    if tracking_script:
        doc.web_form_script = (doc.web_form_script or "") + "\n\n" + tracking_script


def validate_tracking_settings(doc, method):
    """Validate tracking settings for web form"""
    if doc.get("trackflow_tracking_enabled") and not doc.get("trackflow_conversion_goal"):
        frappe.throw(_("Please set a conversion goal for tracking"))


def on_web_form_submit(doc, method):
    """Track web form submissions"""
    # Skip if this is not a web form submission or if we're in a migration context
    if doc.doctype != "Web Form":
        return
    
    # Check if we're in a web context (not during migration or background job)
    if not hasattr(frappe.local, 'request') or not frappe.local.request:
        return
        
    # Check if tracking is enabled
    try:
        settings = frappe.get_doc("TrackFlow Settings", "TrackFlow Settings")
        if not settings.enable_tracking:
            return
    except:
        return
        
    # Get the web form
    try:
        web_form_name = doc.get("web_form")
        if not web_form_name:
            return
            
        web_form = frappe.get_doc("Web Form", web_form_name)
        
        # Check if tracking is enabled for this form
        if not web_form.get("trackflow_tracking_enabled"):
            return
            
        # Track the conversion
        from trackflow.tracking import track_conversion
        
        visitor_id = frappe.request.cookies.get('trackflow_visitor')
        if visitor_id:
            conversion_type = web_form.get("trackflow_conversion_goal") or "form_submission"
            
            track_conversion(
                visitor_id=visitor_id,
                conversion_type=conversion_type,
                metadata={
                    "form_name": web_form_name,
                    "doctype": doc.doctype,
                    "doc_name": doc.name,
                    "source": frappe.form_dict.get("utm_source"),
                    "medium": frappe.form_dict.get("utm_medium"),
                    "campaign": frappe.form_dict.get("utm_campaign")
                }
            )
            
    except Exception as e:
        frappe.log_error(f"Error tracking web form submission: {str(e)}")


def get_web_form_tracking_script(web_form):
    """Get tracking script for web form"""
    return """
    // TrackFlow Web Form Tracking
    (function() {
        var form = document.querySelector('form');
        if (form) {
            form.addEventListener('submit', function(e) {
                if (window.trackflow && window.trackflow.push) {
                    window.trackflow.push('track', 'form_start', {
                        form_name: '""" + web_form.name + """',
                        form_title: '""" + web_form.title + """'
                    });
                }
            });
        }
    })();
    """


def update_web_form_context(context):
    """Update web form context with tracking data"""
    # Skip if not in web context
    if not hasattr(frappe.local, 'request'):
        return context
        
    # Add tracking script if enabled
    try:
        settings = frappe.get_doc("TrackFlow Settings", "TrackFlow Settings")
        if settings.enable_tracking:
            from trackflow.utils import get_tracking_script
            context.trackflow_script = get_tracking_script()
    except:
        pass
        
    return context


def get_tracking_script():
    """
    Get the tracking script to inject into web forms
    """
    try:
        settings = frappe.get_doc("TrackFlow Settings", "TrackFlow Settings")
        if not settings.enable_tracking:
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
