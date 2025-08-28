import frappe
from frappe import _

def on_lead_create(doc, method):
    """Track lead creation with TrackFlow"""
    try:
        # Check if lead has tracking information
        if hasattr(doc, 'custom_trackflow_visitor_id') and doc.custom_trackflow_visitor_id:
            # Link lead to visitor
            visitor_id = doc.custom_trackflow_visitor_id
            
            # Update visitor profile
            if frappe.db.exists("Visitor", visitor_id):
                visitor = frappe.get_doc("Visitor", visitor_id)
                visitor.lead = doc.name
                visitor.lead_created_date = frappe.utils.now()
                visitor.save(ignore_permissions=True)
            
            # Track conversion if from campaign
            if doc.custom_trackflow_campaign:
                track_conversion(doc, "lead_created")
                
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "TrackFlow Lead Create Error")

def on_lead_update(doc, method):
    """Track lead status changes"""
    try:
        # Check if status changed
        if doc.has_value_changed("status"):
            # Create status change record
            status_change = frappe.new_doc("Lead Status Change")
            status_change.lead = doc.name
            status_change.from_status = doc.get_doc_before_save().status if doc.get_doc_before_save() else None
            status_change.to_status = doc.status
            status_change.changed_by = frappe.session.user
            
            # Link to campaign if exists
            if hasattr(doc, 'custom_trackflow_campaign'):
                status_change.campaign = doc.custom_trackflow_campaign
                
            status_change.insert(ignore_permissions=True)
            
            # Track conversion for qualified leads
            if doc.status in ["Qualified", "Converted"]:
                track_conversion(doc, "lead_qualified")
                
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "TrackFlow Lead Update Error")

def on_lead_trash(doc, method):
    """Clean up tracking data when lead is deleted"""
    try:
        # Remove visitor association
        if hasattr(doc, 'custom_trackflow_visitor_id') and doc.custom_trackflow_visitor_id:
            frappe.db.set_value("Visitor", doc.custom_trackflow_visitor_id, 
                              "lead", None, update_modified=False)
            
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "TrackFlow Lead Trash Error")

def track_conversion(doc, conversion_type):
    """Track conversion event"""
    try:
        conversion = frappe.new_doc("Link Conversion")
        conversion.doctype_name = "CRM Lead"
        conversion.document_name = doc.name
        conversion.conversion_type = conversion_type
        conversion.campaign = doc.custom_trackflow_campaign if hasattr(doc, 'custom_trackflow_campaign') else None
        conversion.source = doc.custom_trackflow_source if hasattr(doc, 'custom_trackflow_source') else None
        conversion.medium = doc.custom_trackflow_medium if hasattr(doc, 'custom_trackflow_medium') else None
        conversion.visitor_id = doc.custom_trackflow_visitor_id if hasattr(doc, 'custom_trackflow_visitor_id') else None
        conversion.insert(ignore_permissions=True)
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "TrackFlow Conversion Tracking Error")

@frappe.whitelist()
def get_lead_tracking_data(lead):
    """Get tracking data for a lead"""
    try:
        lead_doc = frappe.get_doc("CRM Lead", lead)
        
        data = {
            "visitor_id": lead_doc.custom_trackflow_visitor_id if hasattr(lead_doc, 'custom_trackflow_visitor_id') else None,
            "source": lead_doc.custom_trackflow_source if hasattr(lead_doc, 'custom_trackflow_source') else None,
            "medium": lead_doc.custom_trackflow_medium if hasattr(lead_doc, 'custom_trackflow_medium') else None,
            "campaign": lead_doc.custom_trackflow_campaign if hasattr(lead_doc, 'custom_trackflow_campaign') else None,
            "first_touch_date": lead_doc.custom_trackflow_first_touch_date if hasattr(lead_doc, 'custom_trackflow_first_touch_date') else None,
            "last_touch_date": lead_doc.custom_trackflow_last_touch_date if hasattr(lead_doc, 'custom_trackflow_last_touch_date') else None,
            "touch_count": lead_doc.custom_trackflow_touch_count if hasattr(lead_doc, 'custom_trackflow_touch_count') else 0
        }
        
        # Get click events
        clicks = frappe.get_all("Click Event", 
            filters={"visitor_id": data["visitor_id"]},
            fields=["name", "tracked_link", "creation", "utm_source", "utm_medium", "utm_campaign"],
            order_by="creation desc",
            limit=10
        )
        
        data["click_history"] = clicks
        
        return data
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "TrackFlow Get Lead Data Error")
        return {}
