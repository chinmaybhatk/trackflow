import frappe
from frappe import _
from frappe.utils import flt, nowdate

def after_insert(doc, method):
    """Track deal creation with attribution"""
    try:
        if hasattr(doc, 'trackflow_visitor_id') and doc.trackflow_visitor_id:
            # Link deal to visitor
            visitor_id = doc.trackflow_visitor_id
            
            if frappe.db.exists("Visitor", visitor_id):
                visitor = frappe.get_doc("Visitor", visitor_id)
                visitor.deal = doc.name
                visitor.deal_created_date = frappe.utils.now()
                visitor.save(ignore_permissions=True)
            
            # Track initial attribution
            create_attribution_record(doc)
            
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "TrackFlow Deal Create Error")

def on_update(doc, method):
    """Track deal stage changes"""
    try:
        if doc.has_value_changed("deal_stage"):
            # Create stage change record
            stage_change = frappe.new_doc("Deal Stage Change")
            stage_change.deal = doc.name
            stage_change.from_stage = doc.get_doc_before_save().deal_stage if doc.get_doc_before_save() else None
            stage_change.to_stage = doc.deal_stage
            stage_change.changed_by = frappe.session.user
            
            if hasattr(doc, 'trackflow_last_touch_source'):
                stage_change.campaign = doc.trackflow_last_touch_source
                
            stage_change.insert(ignore_permissions=True)
            
            # Track conversion for won deals
            if doc.status == "Won":
                track_deal_conversion(doc)
                
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "TrackFlow Deal Update Error")

def calculate_attribution(doc, method):
    """Calculate marketing attribution for won deals"""
    try:
        if doc.status != "Won":
            return
            
        # Get all touchpoints for this deal
        touchpoints = get_deal_touchpoints(doc)
        
        if not touchpoints:
            return
            
        # Get attribution model using shared function
        attribution_model = get_default_attribution_model_cached()
        
        if not attribution_model:
            frappe.log_error("No attribution model available", "Deal Attribution Error")
            return
            
        # Convert touchpoints using shared function
        formatted_touchpoints = format_touchpoints_for_attribution(touchpoints)
        
        # Calculate attribution using Attribution Model engine
        attribution_result = attribution_model.calculate_attribution(formatted_touchpoints, doc.annual_revenue or 0)
        
        # Save attribution records
        for channel, data in attribution_result.items():
            # Find corresponding touchpoint for additional details
            touchpoint_data = next((tp for tp in touchpoints if tp.get("source") == channel), {})
            
            attribution = frappe.new_doc("Deal Attribution")
            attribution.deal = doc.name
            attribution.attribution_model = attribution_model.name
            attribution.deal_value = doc.annual_revenue or 0
            attribution.touchpoint_type = channel.title()  # Convert to title case
            attribution.touchpoint_source = channel
            attribution.touchpoint_campaign = touchpoint_data.get("campaign")
            attribution.touchpoint_medium = touchpoint_data.get("medium")
            attribution.touchpoint_timestamp = touchpoint_data.get("date") or frappe.utils.now()
            attribution.attribution_weight = (data.get("credit", 0) * 100)  # Convert decimal to percentage
            attribution.attributed_value = data.get("value", 0)
            
            # Set position in journey if available
            if touchpoint_data.get("position"):
                attribution.position_in_journey = touchpoint_data.get("position")
                
            attribution.insert(ignore_permissions=True)
            
        # Update deal with attribution summary
        doc.trackflow_attribution_model = attribution_model.model_type
        doc.trackflow_marketing_influenced = 1
        doc.save()
            
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "TrackFlow Attribution Calculation Error")

def format_touchpoints_for_attribution(touchpoints):
    """Convert touchpoints to format expected by Attribution Model"""
    formatted_touchpoints = []
    for tp in touchpoints:
        formatted_touchpoints.append({
            "channel": tp.get("source", "direct"),
            "timestamp": tp.get("date"),
            "campaign": tp.get("campaign"),
            "source": tp.get("source"), 
            "medium": tp.get("medium")
        })
    return formatted_touchpoints

def get_default_attribution_model_cached():
    """Get default attribution model with caching"""
    from trackflow.trackflow.doctype.attribution_model.attribution_model import get_default_attribution_model
    return get_default_attribution_model()

def get_deal_touchpoints(doc):
    """Get all marketing touchpoints for a deal"""
    touchpoints = []
    
    try:
        # Get visitor ID
        visitor_id = doc.trackflow_visitor_id if hasattr(doc, 'trackflow_visitor_id') else None
        
        if not visitor_id:
            return touchpoints
            
        # Get all click events for visitor
        clicks = frappe.get_all("Click Event",
            filters={"visitor_id": visitor_id},
            fields=["name", "campaign", "utm_source", "utm_medium", "utm_campaign", "creation"],
            order_by="creation asc"
        )
        
        for click in clicks:
            touchpoints.append({
                "type": "click",
                "campaign": click.campaign or click.utm_campaign,
                "source": click.utm_source,
                "medium": click.utm_medium,
                "date": click.creation
            })
            
        # Get email interactions
        email_logs = frappe.get_all("Email Campaign Log",
            filters={"visitor_id": visitor_id},
            fields=["campaign", "action", "creation"],
            order_by="creation asc"
        )
        
        for log in email_logs:
            touchpoints.append({
                "type": "email",
                "campaign": log.campaign,
                "source": "email",
                "medium": "email",
                "date": log.creation
            })
            
        return touchpoints
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "TrackFlow Get Touchpoints Error")
        return []

# Deprecated: calculate_attribution_credits function removed
# Attribution logic now handled by Attribution Model DocType

def track_deal_conversion(doc):
    """Track deal conversion"""
    try:
        conversion = frappe.new_doc("Link Conversion")
        conversion.doctype_name = "CRM Deal"
        conversion.document_name = doc.name
        conversion.conversion_type = "deal_won"
        conversion.conversion_value = doc.annual_revenue
        conversion.campaign = doc.trackflow_last_touch_source if hasattr(doc, 'trackflow_last_touch_source') else None
        conversion.source = doc.trackflow_first_touch_source if hasattr(doc, 'trackflow_first_touch_source') else None
        conversion.visitor_id = doc.trackflow_visitor_id if hasattr(doc, 'trackflow_visitor_id') else None
        conversion.insert(ignore_permissions=True)
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "TrackFlow Deal Conversion Error")

def create_attribution_record(doc):
    """Create initial attribution record"""
    try:
        if hasattr(doc, 'trackflow_last_touch_source') and doc.trackflow_last_touch_source:
            link_assoc = frappe.new_doc("Deal Link Association")
            link_assoc.deal = doc.name
            link_assoc.campaign = doc.trackflow_last_touch_source
            link_assoc.source = doc.trackflow_first_touch_source if hasattr(doc, 'trackflow_first_touch_source') else None
            link_assoc.insert(ignore_permissions=True)
            
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "TrackFlow Attribution Record Error")


@frappe.whitelist()
def get_deal_attribution_report(deal_name):
    """Get attribution report for a deal"""
    try:
        deal = frappe.get_doc("CRM Deal", deal_name)
        
        # Get visitor ID and attribution data
        visitor_id = getattr(deal, 'trackflow_visitor_id', None)
        if not visitor_id:
            return {"error": "No visitor tracking data found for this deal"}
        
        # Get all touchpoints for this deal
        touchpoints = get_deal_touchpoints(deal)
        
        # Get attribution summary
        attribution_summary = {
            "deal_name": deal.name,
            "deal_value": deal.annual_revenue or 0,
            "attribution_model": getattr(deal, 'trackflow_attribution_model', 'Last Touch'),
            "visitor_id": visitor_id,
            "touchpoint_count": len(touchpoints),
            "touchpoints": touchpoints[:10],  # Limit to latest 10
        }
        
        # Check for existing attribution records first
        existing_attributions = frappe.get_all(
            "Deal Attribution",
            filters={"deal": deal_name},
            fields=["touchpoint_type", "touchpoint_source", "attribution_weight", "attributed_value"]
        )
        
        if existing_attributions:
            # Use stored attribution records
            attribution_breakdown = {}
            for attr in existing_attributions:
                source = attr.touchpoint_source or attr.touchpoint_type
                attribution_breakdown[source] = {
                    "credit": attr.attribution_weight / 100,  # Convert percentage to decimal
                    "value": attr.attributed_value
                }
            attribution_summary["attribution_breakdown"] = attribution_breakdown
        elif touchpoints:
            # Calculate attribution breakdown if no stored records
            attribution_model = get_default_attribution_model_cached()
            
            if attribution_model:
                formatted_touchpoints = format_touchpoints_for_attribution(touchpoints)
                attribution_result = attribution_model.calculate_attribution(formatted_touchpoints, deal.annual_revenue or 0)
                attribution_summary["attribution_breakdown"] = attribution_result
        
        return attribution_summary
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Deal Attribution Report Error")
        return {"error": str(e)}
