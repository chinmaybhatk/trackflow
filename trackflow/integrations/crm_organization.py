import frappe
from frappe import _

def after_insert(doc, method):
    """Track organization creation"""
    try:
        if hasattr(doc, 'custom_trackflow_visitor_id') and doc.custom_trackflow_visitor_id:
            # Link organization to visitor
            visitor_id = doc.custom_trackflow_visitor_id
            
            if frappe.db.exists("Visitor", visitor_id):
                visitor = frappe.get_doc("Visitor", visitor_id)
                visitor.organization = doc.name
                visitor.organization_created_date = frappe.utils.now()
                visitor.save(ignore_permissions=True)
            
            # Track conversion
            if doc.custom_trackflow_campaign:
                track_conversion(doc, "organization_created")
                
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "TrackFlow Organization Create Error")

def on_update(doc, method):
    """Update organization engagement score based on interactions"""
    try:
        if not hasattr(doc, 'custom_trackflow_visitor_id') or not doc.custom_trackflow_visitor_id:
            return
            
        # Calculate engagement score
        engagement_score = calculate_engagement_score(doc)
        
        # Update if changed
        if engagement_score != doc.custom_trackflow_engagement_score:
            frappe.db.set_value("CRM Organization", doc.name, 
                              "custom_trackflow_engagement_score", engagement_score,
                              update_modified=False)
            
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "TrackFlow Organization Update Error")

def calculate_engagement_score(doc):
    """Calculate engagement score based on various factors"""
    try:
        score = 0
        visitor_id = doc.custom_trackflow_visitor_id
        
        # Click events (1 point per click, max 20)
        clicks = frappe.db.count("Click Event", {"visitor_id": visitor_id})
        score += min(clicks, 20)
        
        # Email opens (2 points per open, max 20)
        email_opens = frappe.db.count("Email Campaign Log", 
                                     {"visitor_id": visitor_id, "action": "opened"})
        score += min(email_opens * 2, 20)
        
        # Email clicks (3 points per click, max 30)
        email_clicks = frappe.db.count("Email Campaign Log",
                                      {"visitor_id": visitor_id, "action": "clicked"})
        score += min(email_clicks * 3, 30)
        
        # Form submissions (10 points per submission, max 30)
        form_submissions = frappe.db.count("Web Form Submission",
                                          {"custom_trackflow_visitor_id": visitor_id})
        score += min(form_submissions * 10, 30)
        
        # Deals associated (20 points if any deals)
        deals = frappe.db.count("CRM Deal", 
                               {"custom_trackflow_visitor_id": visitor_id})
        if deals > 0:
            score += 20
            
        return min(score, 100)  # Cap at 100
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "TrackFlow Engagement Score Error")
        return 0

def track_conversion(doc, conversion_type):
    """Track organization conversion"""
    try:
        conversion = frappe.new_doc("Link Conversion")
        conversion.doctype_name = "CRM Organization"
        conversion.document_name = doc.name
        conversion.conversion_type = conversion_type
        conversion.campaign = doc.custom_trackflow_campaign if hasattr(doc, 'custom_trackflow_campaign') else None
        conversion.source = doc.custom_trackflow_source if hasattr(doc, 'custom_trackflow_source') else None
        conversion.medium = doc.custom_trackflow_medium if hasattr(doc, 'custom_trackflow_medium') else None
        conversion.visitor_id = doc.custom_trackflow_visitor_id if hasattr(doc, 'custom_trackflow_visitor_id') else None
        conversion.insert(ignore_permissions=True)
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "TrackFlow Organization Conversion Error")

@frappe.whitelist()
def get_organization_journey(organization):
    """Get complete journey for an organization"""
    try:
        org = frappe.get_doc("CRM Organization", organization)
        visitor_id = org.custom_trackflow_visitor_id if hasattr(org, 'custom_trackflow_visitor_id') else None
        
        if not visitor_id:
            return {"touchpoints": [], "engagement_score": 0}
            
        # Get all touchpoints
        touchpoints = []
        
        # Click events
        clicks = frappe.get_all("Click Event",
            filters={"visitor_id": visitor_id},
            fields=["name", "tracked_link", "creation", "utm_source", "utm_medium", "utm_campaign"],
            order_by="creation desc"
        )
        
        for click in clicks:
            touchpoints.append({
                "type": "click",
                "date": str(click.creation),
                "source": click.utm_source,
                "medium": click.utm_medium,
                "campaign": click.utm_campaign
            })
            
        # Email interactions
        emails = frappe.get_all("Email Campaign Log",
            filters={"visitor_id": visitor_id},
            fields=["campaign", "action", "creation"],
            order_by="creation desc"
        )
        
        for email in emails:
            touchpoints.append({
                "type": f"email_{email.action}",
                "date": str(email.creation),
                "campaign": email.campaign
            })
            
        # Sort by date
        touchpoints.sort(key=lambda x: x["date"], reverse=True)
        
        return {
            "touchpoints": touchpoints[:50],  # Latest 50 touchpoints
            "engagement_score": org.custom_trackflow_engagement_score or 0,
            "total_touchpoints": len(touchpoints),
            "first_touch_date": touchpoints[-1]["date"] if touchpoints else None,
            "last_touch_date": touchpoints[0]["date"] if touchpoints else None
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "TrackFlow Get Organization Journey Error")
        return {"touchpoints": [], "engagement_score": 0}
