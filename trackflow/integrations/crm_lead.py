import frappe
from frappe import _
from trackflow.trackflow.utils.error_handler import handle_error, log_activity, IntegrationError


def _resolve_visitor_id_from_request():
    """Find a TrackFlow visitor id from the current request, if any.

    Looks at, in order: form_dict (works for web form submissions and API
    calls), then the trackflow_visitor cookie set by the redirect handler.
    Returns None outside a request context.
    """
    try:
        form_dict = getattr(frappe, "form_dict", None)
        if form_dict:
            v = form_dict.get("tf_visitor") or form_dict.get("trackflow_visitor")
            if v:
                return v
        request = getattr(frappe, "request", None)
        if request and getattr(request, "cookies", None):
            return request.cookies.get("trackflow_visitor")
    except Exception:
        pass
    return None


def _resolve_attribution_from_visitor(visitor_id):
    """Look up the visitor's most recent click and return source/medium/campaign."""
    if not visitor_id:
        return {}
    visitor_name = frappe.db.get_value("Visitor", {"visitor_id": visitor_id}, "name")
    if not visitor_name:
        return {}
    last_click = frappe.db.sql(
        """
        SELECT tracked_link
        FROM `tabClick Event`
        WHERE visitor_id = %s
        ORDER BY click_timestamp DESC
        LIMIT 1
        """,
        visitor_id,
        as_dict=True,
    )
    if not last_click:
        return {}
    link = frappe.db.get_value(
        "Tracked Link",
        last_click[0].tracked_link,
        ["source", "medium", "campaign"],
        as_dict=True,
    )
    return link or {}


def before_lead_create(doc, method):
    """Capture the originating visitor from the current request.

    If the lead is being created from a web form submission (or any request)
    that carries a tf_visitor parameter / trackflow_visitor cookie, stamp the
    visitor id and best-known attribution onto the lead before insert so the
    downstream after_insert hook can link visitor -> lead.
    """
    if doc.get("trackflow_visitor_id"):
        return
    visitor_id = _resolve_visitor_id_from_request()
    if not visitor_id:
        return
    doc.trackflow_visitor_id = visitor_id
    attribution = _resolve_attribution_from_visitor(visitor_id)
    if attribution.get("source") and not doc.get("trackflow_source"):
        doc.trackflow_source = attribution["source"]
    if attribution.get("medium") and not doc.get("trackflow_medium"):
        doc.trackflow_medium = attribution["medium"]
    if attribution.get("campaign") and not doc.get("trackflow_campaign"):
        doc.trackflow_campaign = attribution["campaign"]

    # Make sure a Visitor record exists so the after_insert hook can link it.
    try:
        from trackflow.trackflow.utils import upsert_visitor
        upsert_visitor(visitor_id)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "TrackFlow visitor upsert (before_lead_create)")


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
                track_conversion(doc, "Lead", visitor_id, campaign)
                
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
                track_conversion(doc, "Lead", visitor_id, campaign)

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
    """Record a Conversion event.

    A Conversion is a downstream outcome (lead created, signup, purchase,
    form submission, etc.) attributed back to the visitor's most recent
    tracked-link click. Click Event = the visit; Conversion = what
    happened next.
    """
    try:
        last_click = frappe.db.sql(
            """
            SELECT name, tracked_link
            FROM `tabClick Event`
            WHERE visitor_id = %s
            ORDER BY click_timestamp DESC
            LIMIT 1
            """,
            visitor_id,
            as_dict=True,
        )
        if not last_click:
            # No tracked click for this visitor — Conversion requires both
            # click_event and tracked_link, so we cannot record one. Skip silently.
            return

        conversion = frappe.new_doc("Conversion")
        conversion.visitor_id = visitor_id
        conversion.click_event = last_click[0].name
        conversion.tracked_link = last_click[0].tracked_link
        conversion.conversion_type = conversion_type
        conversion.conversion_timestamp = frappe.utils.now()
        if campaign:
            conversion.campaign = campaign
        conversion.source_doctype = "CRM Lead"
        conversion.source_document = doc.name
        conversion.lead = doc.name
        conversion.conversion_metadata = frappe.as_json({
            "doctype": "CRM Lead",
            "document": doc.name,
            "lead_name": doc.lead_name,
            "email": doc.email,
            "status": doc.status,
            "source": doc.get("trackflow_source") or doc.get("source"),
            "medium": doc.get("trackflow_medium"),
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
    
    # Get visitor click + conversion history if visitor exists
    if data["visitor_id"]:
        visitor_name = frappe.db.get_value("Visitor", {"visitor_id": data["visitor_id"]}, "name")

        if visitor_name:
            # Get click events
            clicks = frappe.get_all("Click Event",
                filters={"visitor_id": data["visitor_id"]},
                fields=["name", "tracked_link", "click_timestamp", "ip_address", "user_agent"],
                order_by="click_timestamp desc",
                limit=10
            )
            data["click_history"] = clicks

            # Get conversions
            conversions = frappe.get_all("Conversion",
                filters={"visitor_id": data["visitor_id"]},
                fields=["name", "conversion_type", "conversion_timestamp", "conversion_value"],
                order_by="conversion_timestamp desc"
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
