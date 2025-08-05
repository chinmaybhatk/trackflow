import frappe
from frappe import _
import json

def on_web_form_submit(doc, method):
    """Track web form submissions"""
    # Get visitor ID from cookies or session
    visitor_id = get_visitor_id()
    
    if not visitor_id:
        return
    
    # Get campaign from URL parameters or session
    campaign = get_campaign_from_context()
    
    # Create form submission record
    submission = frappe.new_doc("Form Submission")
    submission.form_name = doc.web_form
    submission.form_title = frappe.db.get_value("Web Form", doc.web_form, "title")
    submission.visitor_id = visitor_id
    submission.campaign = campaign
    submission.submission_date = frappe.utils.now()
    submission.form_data = json.dumps(doc.as_dict())
    
    # Get session details
    session = frappe.db.get_value(
        "Visitor Session",
        {"visitor_id": visitor_id},
        ["name", "utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"],
        as_dict=1,
        order_by="creation desc"
    )
    
    if session:
        submission.session = session.name
        submission.utm_source = session.utm_source
        submission.utm_medium = session.utm_medium
        submission.utm_campaign = session.utm_campaign
        submission.utm_content = session.utm_content
        submission.utm_term = session.utm_term
    
    submission.insert(ignore_permissions=True)
    
    # Create conversion record
    conversion = frappe.new_doc("TrackFlow Conversion")
    conversion.visitor_id = visitor_id
    conversion.campaign = campaign
    conversion.conversion_type = "Form Submission"
    conversion.conversion_date = frappe.utils.now()
    conversion.form_id = doc.web_form
    conversion.form_title = submission.form_title
    
    if session:
        conversion.utm_source = session.utm_source
        conversion.utm_medium = session.utm_medium
        conversion.utm_campaign = session.utm_campaign
        conversion.utm_content = session.utm_content
        conversion.utm_term = session.utm_term
    
    conversion.insert(ignore_permissions=True)
    
    # If web form creates a lead, handle lead attribution
    if doc.doctype == "Lead" and hasattr(doc, "name"):
        handle_lead_attribution(doc, visitor_id, campaign)
    
    # Update campaign metrics
    if campaign:
        from trackflow.trackflow.doctype.trackflow_campaign.trackflow_campaign import update_campaign_metrics
        campaign_doc = frappe.get_doc("TrackFlow Campaign", campaign)
        update_campaign_metrics(campaign_doc)

def handle_lead_attribution(lead, visitor_id, campaign):
    """Create lead attribution when web form creates a lead"""
    # Create lead link association
    lead_link = frappe.new_doc("Lead Link Association")
    lead_link.lead = lead.name
    lead_link.lead_name = lead.lead_name or lead.email_id
    lead_link.visitor_id = visitor_id
    lead_link.campaign = campaign
    lead_link.insert(ignore_permissions=True)
    
    # Create conversion for lead creation
    conversion = frappe.new_doc("TrackFlow Conversion")
    conversion.visitor_id = visitor_id
    conversion.campaign = campaign
    conversion.conversion_type = "Lead Created"
    conversion.conversion_date = frappe.utils.now()
    conversion.lead = lead.name
    conversion.lead_name = lead.lead_name or lead.email_id
    conversion.email_id = lead.email_id
    conversion.phone = lead.mobile_no or lead.phone
    conversion.insert(ignore_permissions=True)
    
    # Send notification
    from trackflow.trackflow.notifications import send_conversion_notification
    send_conversion_notification(conversion)

def get_visitor_id():
    """Get visitor ID from cookies or session"""
    # Check cookies
    if frappe.request and frappe.request.cookies:
        visitor_id = frappe.request.cookies.get("tf_visitor_id")
        if visitor_id:
            return visitor_id
    
    # Check session
    if frappe.session and frappe.session.data:
        visitor_id = frappe.session.data.get("tf_visitor_id")
        if visitor_id:
            return visitor_id
    
    return None

def get_campaign_from_context():
    """Get campaign from URL parameters or session"""
    campaign = None
    
    # Check form dict (URL parameters)
    if frappe.form_dict:
        campaign = frappe.form_dict.get("tf_campaign") or frappe.form_dict.get("utm_campaign")
    
    # Check session
    if not campaign and frappe.session and frappe.session.data:
        campaign = frappe.session.data.get("tf_campaign")
    
    # Validate campaign exists
    if campaign and frappe.db.exists("TrackFlow Campaign", campaign):
        return campaign
    
    return None

def inject_tracking_script(context):
    """Inject TrackFlow tracking script into web forms"""
    if context.get("doctype") == "Web Form":
        # Get tracking script
        script_url = frappe.utils.get_url("/api/method/trackflow.api.tracking.get_tracking_script")
        
        # Add to context
        if not context.get("script_includes"):
            context.script_includes = []
        
        context.script_includes.append(script_url)
        
        # Add form tracking code
        tracking_code = """
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Track form views
            if (window.TrackFlow && window.TrackFlow.track) {
                window.TrackFlow.track('form_view', {
                    form_id: '{form_id}',
                    form_title: '{form_title}'
                });
            }
            
            // Track form field interactions
            var formFields = document.querySelectorAll('input, select, textarea');
            var trackedFields = new Set();
            
            formFields.forEach(function(field) {
                field.addEventListener('focus', function() {
                    if (!trackedFields.has(field.name) && window.TrackFlow && window.TrackFlow.track) {
                        trackedFields.add(field.name);
                        window.TrackFlow.track('form_field_interaction', {
                            form_id: '{form_id}',
                            field_name: field.name,
                            field_type: field.type
                        });
                    }
                });
            });
            
            // Track form submission
            var form = document.querySelector('form');
            if (form) {
                form.addEventListener('submit', function() {
                    if (window.TrackFlow && window.TrackFlow.track) {
                        window.TrackFlow.track('form_submit_attempt', {
                            form_id: '{form_id}',
                            form_title: '{form_title}'
                        });
                    }
                });
            }
        });
        </script>
        """.format(
            form_id=context.name,
            form_title=context.title
        )
        
        context.tracking_code = tracking_code

def get_form_analytics(web_form_name):
    """Get analytics for a web form"""
    analytics = {
        "total_views": 0,
        "unique_viewers": 0,
        "submissions": 0,
        "conversion_rate": 0,
        "field_interactions": {},
        "abandonment_rate": 0,
        "avg_time_to_submit": None,
        "top_sources": [],
        "daily_submissions": []
    }
    
    # Get form views from page views
    form_url = frappe.utils.get_url("/web-form/" + web_form_name)
    
    views = frappe.db.sql("""
        SELECT 
            COUNT(*) as total_views,
            COUNT(DISTINCT visitor_id) as unique_viewers
        FROM `tabPage View`
        WHERE page_url LIKE %s
        AND docstatus < 2
    """, ("%" + form_url + "%",), as_dict=1)[0]
    
    analytics["total_views"] = views.total_views
    analytics["unique_viewers"] = views.unique_viewers
    
    # Get submissions
    submissions = frappe.db.count(
        "Form Submission",
        filters={
            "form_name": web_form_name,
            "docstatus": ["<", 2]
        }
    )
    
    analytics["submissions"] = submissions
    
    # Calculate conversion rate
    if analytics["unique_viewers"] > 0:
        analytics["conversion_rate"] = round(
            (analytics["submissions"] / analytics["unique_viewers"]) * 100, 2
        )
    
    # Get field interaction data
    field_data = frappe.db.sql("""
        SELECT 
            field_name,
            COUNT(DISTINCT visitor_id) as interactions
        FROM `tabForm Field Interaction`
        WHERE form_id = %s
        AND docstatus < 2
        GROUP BY field_name
        ORDER BY interactions DESC
    """, web_form_name, as_dict=1)
    
    analytics["field_interactions"] = {f.field_name: f.interactions for f in field_data}
    
    # Calculate abandonment rate
    started_forms = frappe.db.sql("""
        SELECT COUNT(DISTINCT visitor_id) as count
        FROM `tabForm Field Interaction`
        WHERE form_id = %s
        AND docstatus < 2
    """, web_form_name)[0][0]
    
    if started_forms > 0:
        analytics["abandonment_rate"] = round(
            ((started_forms - submissions) / started_forms) * 100, 2
        )
    
    # Get average time to submit
    avg_time = frappe.db.sql("""
        SELECT AVG(TIMESTAMPDIFF(SECOND, pv.view_date, fs.submission_date)) as avg_time
        FROM `tabForm Submission` fs
        INNER JOIN `tabPage View` pv ON pv.visitor_id = fs.visitor_id
        WHERE fs.form_name = %s
        AND pv.page_url LIKE %s
        AND fs.docstatus < 2
        AND pv.docstatus < 2
    """, (web_form_name, "%" + form_url + "%"))[0][0]
    
    if avg_time:
        analytics["avg_time_to_submit"] = format_duration(avg_time)
    
    # Get top sources
    sources = frappe.db.sql("""
        SELECT 
            COALESCE(utm_source, 'Direct') as source,
            COUNT(*) as count
        FROM `tabForm Submission`
        WHERE form_name = %s
        AND docstatus < 2
        GROUP BY utm_source
        ORDER BY count DESC
        LIMIT 5
    """, web_form_name, as_dict=1)
    
    analytics["top_sources"] = sources
    
    # Get daily submissions
    daily = frappe.db.sql("""
        SELECT 
            DATE(submission_date) as date,
            COUNT(*) as submissions
        FROM `tabForm Submission`
        WHERE form_name = %s
        AND docstatus < 2
        AND submission_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        GROUP BY DATE(submission_date)
        ORDER BY date
    """, web_form_name, as_dict=1)
    
    analytics["daily_submissions"] = daily
    
    return analytics

def format_duration(seconds):
    """Format duration in seconds to human readable format"""
    if not seconds:
        return "0s"
    
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    
    if minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"
