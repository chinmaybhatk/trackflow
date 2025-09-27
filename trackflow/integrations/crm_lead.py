import frappe
from frappe import _
from trackflow.trackflow.utils.error_handler import handle_error, log_activity, IntegrationError

@handle_error(error_type="CRM Lead Create", return_response=False)
def on_lead_create(doc, method):
    """Track lead creation with TrackFlow"""
    try:
        # Validate doc object
        if not doc or not hasattr(doc, 'name'):
            frappe.log_error("Invalid doc object in TrackFlow lead create hook", "TrackFlow Lead Create")
            return
            
        # Check if lead has tracking information
        visitor_id = doc.get('trackflow_visitor_id')
        
        if visitor_id:
            # Link lead to visitor
            if frappe.db.exists("Visitor", {"visitor_id": visitor_id}):
                visitor = frappe.db.get_value("Visitor", {"visitor_id": visitor_id}, "name")
                frappe.db.set_value("Visitor", visitor, {
                    "crm_lead": doc.name,
                    "lead_created_date": frappe.utils.now()
                })
                
                # Log activity
                log_activity("lead_created", {
                    "lead": doc.name,
                    "visitor_id": visitor_id,
                    "campaign": doc.get('trackflow_campaign')
                })
            
            # Track conversion if from campaign
            campaign = doc.get('trackflow_campaign')
            if campaign:
                track_conversion(doc, "lead_created", visitor_id, campaign)
                
    except Exception as e:
        # Log error but don't block lead creation
        frappe.log_error(f"TrackFlow lead tracking error: {str(e)}", "TrackFlow Lead Create Error")
        pass

@handle_error(error_type="CRM Lead Update", return_response=False)
def on_lead_update(doc, method):
    """Track lead status changes"""
    # Check if status changed
    if doc.has_value_changed("status"):
        old_status = doc.get_doc_before_save().status if doc.get_doc_before_save() else None
        
        # Create status change record
        if frappe.db.exists("DocType", "Lead Status Change"):
            status_change = frappe.new_doc("Lead Status Change")
            status_change.lead = doc.name
            status_change.from_status = old_status
            status_change.to_status = doc.status
            status_change.changed_by = frappe.session.user
            status_change.campaign = doc.get('trackflow_campaign')
            status_change.insert(ignore_permissions=True)
        
        # Log activity
        log_activity("lead_status_changed", {
            "lead": doc.name,
            "from_status": old_status,
            "to_status": doc.status
        })
        
        # Track conversion for qualified leads
        if doc.status in ["Qualified", "Converted"]:
            visitor_id = doc.get('trackflow_visitor_id')
            campaign = doc.get('trackflow_campaign')
            if visitor_id:
                track_conversion(doc, "lead_qualified", visitor_id, campaign)

@handle_error(error_type="CRM Lead Trash", return_response=False)
def on_lead_trash(doc, method):
    """Clean up tracking data when lead is deleted"""
    visitor_id = doc.get('trackflow_visitor_id')
    
    if visitor_id:
        # Remove visitor association
        if frappe.db.exists("Visitor", {"visitor_id": visitor_id}):
            visitor = frappe.db.get_value("Visitor", {"visitor_id": visitor_id}, "name")
            frappe.db.set_value("Visitor", visitor, "crm_lead", None, update_modified=False)
        
        # Log activity
        log_activity("lead_deleted", {
            "lead": doc.name,
            "visitor_id": visitor_id
        }, severity="warning")

def track_conversion(doc, conversion_type, visitor_id, campaign=None):
    """Track conversion event"""
    try:
        # Create conversion record using new DocType
        conversion = frappe.new_doc("Conversion")
        
        # Get visitor name
        visitor_name = frappe.db.get_value("Visitor", {"visitor_id": visitor_id}, "name")
        if visitor_name:
            conversion.visitor = visitor_name
        
        conversion.conversion_type = conversion_type
        conversion.conversion_date = frappe.utils.now()
        
        # Add tracking details
        conversion.source = doc.get('trackflow_source') or doc.get('source')
        conversion.medium = doc.get('trackflow_medium')
        conversion.campaign = campaign
        
        # Add metadata
        conversion.metadata = frappe.as_json({
            "doctype": "CRM Lead",
            "document": doc.name,
            "lead_name": doc.lead_name,
            "email": doc.email,
            "status": doc.status
        })
        
        conversion.insert(ignore_permissions=True)
        
    except Exception as e:
        raise IntegrationError(f"Failed to track conversion: {str(e)}")

@frappe.whitelist()
@handle_error(error_type="Get Lead Tracking Data")
def get_lead_tracking_data(lead):
    """Get tracking data for a lead"""
    if not frappe.db.exists("CRM Lead", lead):
        raise IntegrationError(_("Lead not found"))
    
    lead_doc = frappe.get_doc("CRM Lead", lead)
    
    data = {
        "visitor_id": lead_doc.get('trackflow_visitor_id'),
        "source": lead_doc.get('trackflow_source') or lead_doc.get('source'),
        "medium": lead_doc.get('trackflow_medium'),
        "campaign": lead_doc.get('trackflow_campaign'),
        "first_touch_date": lead_doc.get('trackflow_first_touch_date'),
        "last_touch_date": lead_doc.get('trackflow_last_touch_date'),
        "touch_count": lead_doc.get('trackflow_touch_count', 0)
    }
    
    # Get visitor sessions if visitor exists
    if data["visitor_id"]:
        visitor_name = frappe.db.get_value("Visitor", {"visitor_id": data["visitor_id"]}, "name")
        
        if visitor_name:
            # Get visitor sessions
            sessions = frappe.get_all("Visitor Session",
                filters={"visitor": visitor_name},
                fields=["name", "visit_date", "utm_source", "utm_medium", "utm_campaign", "page_views", "duration"],
                order_by="visit_date desc",
                limit=10
            )
            data["session_history"] = sessions
            
            # Get click events
            clicks = frappe.get_all("Click Event",
                filters={"visitor": visitor_name},
                fields=["name", "tracked_link", "click_time", "browser", "device_type"],
                order_by="click_time desc",
                limit=10
            )
            data["click_history"] = clicks
            
            # Get conversions
            conversions = frappe.get_all("Conversion",
                filters={"visitor": visitor_name},
                fields=["name", "conversion_type", "conversion_date", "conversion_value"],
                order_by="conversion_date desc"
            )
            data["conversions"] = conversions
    
    return {"status": "success", "data": data}

@frappe.whitelist()
def link_visitor_to_lead(lead, visitor_id):
    """Link a visitor to an existing lead"""
    try:
        # Validate lead exists
        if not frappe.db.exists("CRM Lead", lead):
            return {"status": "error", "message": _("Lead not found")}
        
        # Validate visitor exists
        if not frappe.db.exists("Visitor", {"visitor_id": visitor_id}):
            return {"status": "error", "message": _("Visitor not found")}
        
        # Update lead
        frappe.db.set_value("CRM Lead", lead, "trackflow_visitor_id", visitor_id)
        
        # Update visitor
        visitor_name = frappe.db.get_value("Visitor", {"visitor_id": visitor_id}, "name")
        frappe.db.set_value("Visitor", visitor_name, "crm_lead", lead)
        
        # Log activity
        log_activity("visitor_linked_to_lead", {
            "lead": lead,
            "visitor_id": visitor_id
        })
        
        frappe.db.commit()
        
        return {"status": "success", "message": _("Visitor linked to lead successfully")}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}
