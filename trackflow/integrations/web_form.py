import frappe
from frappe import _
import json

def inject_tracking_script(doc, method):
    """Auto-inject TrackFlow tracking into web forms"""
    if not hasattr(doc, 'trackflow_tracking_enabled'):
        return
        
    if doc.trackflow_tracking_enabled:
        tracking_script = """
// TrackFlow Web Form Tracking
(function() {
    if (typeof trackflow === 'undefined') {
        window.trackflow = window.trackflow || [];
    }
    
    // Track form view
    trackflow.track('form_view', {
        form_name: '""" + doc.name + """',
        form_title: '""" + doc.title + """'
    });
    
    // Track form field interactions
    frappe.ready(function() {
        // Track field focus
        $('input, select, textarea').on('focus', function() {
            trackflow.track('form_field_focus', {
                form: '""" + doc.name + """',
                field: $(this).attr('name')
            });
        });
        
        // Track form submission attempt
        $('form').on('submit', function() {
            trackflow.track('form_submit_attempt', {
                form: '""" + doc.name + """'
            });
        });
    });
})();
"""
        
        doc.client_script = (doc.client_script or "") + "\n\n" + tracking_script
        
def validate_tracking_settings(doc, method):
    """Validate web form tracking settings"""
    if hasattr(doc, 'trackflow_conversion_goal') and doc.trackflow_conversion_goal:
        # Ensure tracking is enabled if conversion goal is set
        if not doc.trackflow_tracking_enabled:
            doc.trackflow_tracking_enabled = 1
            
def on_web_form_submit(doc, method):
    """Track web form submissions as conversions"""
    try:
        # Check if this is a web form submission
        if not frappe.request or not frappe.request.path:
            return
            
        # Get web form details
        web_form = None
        if "/web-form/" in frappe.request.path:
            form_route = frappe.request.path.split("/web-form/")[1].split("/")[0]
            web_form = frappe.db.get_value("Web Form", 
                                          {"route": form_route}, 
                                          ["name", "trackflow_tracking_enabled", 
                                           "trackflow_conversion_goal"])
            
        if not web_form or not web_form[1]:  # Not tracking enabled
            return
            
        # Get visitor ID from cookie
        visitor_id = frappe.request.cookies.get("tf_visitor_id")
        
        # Create conversion record
        conversion = frappe.new_doc("Link Conversion")
        conversion.doctype_name = doc.doctype
        conversion.document_name = doc.name
        conversion.conversion_type = "web_form_submission"
        conversion.conversion_goal = web_form[2] if len(web_form) > 2 else None
        conversion.visitor_id = visitor_id
        
        # Get UTM parameters from session
        if frappe.session:
            conversion.source = frappe.session.get("utm_source")
            conversion.medium = frappe.session.get("utm_medium")
            conversion.campaign = frappe.session.get("utm_campaign")
            
        conversion.insert(ignore_permissions=True)
        
        # Update visitor if exists
        if visitor_id and frappe.db.exists("Visitor", visitor_id):
            visitor = frappe.get_doc("Visitor", visitor_id)
            visitor.last_seen = frappe.utils.now()
            
            # Link to lead if created
            if doc.doctype == "CRM Lead":
                visitor.lead = doc.name
                visitor.lead_created_date = frappe.utils.now()
                
            visitor.save(ignore_permissions=True)
            
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "TrackFlow Web Form Submission Error")

@frappe.whitelist(allow_guest=True)
def track_form_event(form_name, event_type, field_name=None):
    """API to track form events"""
    try:
        visitor_id = frappe.request.cookies.get("tf_visitor_id")
        
        event = frappe.new_doc("Click Event")
        event.visitor_id = visitor_id
        event.event_type = f"form_{event_type}"
        event.page_url = frappe.request.url
        event.event_data = json.dumps({
            "form": form_name,
            "field": field_name
        })
        event.insert(ignore_permissions=True)
        
        return {"status": "success"}
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "TrackFlow Form Event Error")
        return {"status": "error"}
