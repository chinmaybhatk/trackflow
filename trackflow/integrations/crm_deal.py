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
            
        # Get attribution model
        attribution_model = frappe.db.get_single_value("TrackFlow Settings", "default_attribution_model") or "last_touch"
        
        # Calculate attribution based on model
        attribution_credits = calculate_attribution_credits(touchpoints, attribution_model, doc.annual_revenue)
        
        # Save attribution records
        for touchpoint, credit in attribution_credits.items():
            attribution = frappe.new_doc("Deal Attribution")
            attribution.deal = doc.name
            attribution.campaign = touchpoint.get("campaign")
            attribution.source = touchpoint.get("source")
            attribution.medium = touchpoint.get("medium")
            attribution.touchpoint_date = touchpoint.get("date")
            attribution.attribution_model = attribution_model
            attribution.credit_amount = credit
            attribution.credit_percentage = (credit / doc.annual_revenue * 100) if doc.annual_revenue else 0
            attribution.insert(ignore_permissions=True)
            
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "TrackFlow Attribution Calculation Error")

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

def calculate_attribution_credits(touchpoints, model, total_value):
    """Calculate attribution credits based on model"""
    if not touchpoints:
        return {}
        
    credits = {}
    
    if model == "first_touch":
        # All credit to first touchpoint
        first = touchpoints[0]
        key = f"{first['campaign']}_{first['source']}_{first['medium']}"
        credits[key] = total_value
        
    elif model == "last_touch":
        # All credit to last touchpoint
        last = touchpoints[-1]
        key = f"{last['campaign']}_{last['source']}_{last['medium']}"
        credits[key] = total_value
        
    elif model == "linear":
        # Equal credit to all touchpoints
        credit_per_touch = total_value / len(touchpoints)
        for tp in touchpoints:
            key = f"{tp['campaign']}_{tp['source']}_{tp['medium']}"
            credits[key] = credits.get(key, 0) + credit_per_touch
            
    elif model == "time_decay":
        # More credit to recent touchpoints
        total_weight = sum(range(1, len(touchpoints) + 1))
        for i, tp in enumerate(touchpoints):
            weight = i + 1
            credit = (weight / total_weight) * total_value
            key = f"{tp['campaign']}_{tp['source']}_{tp['medium']}"
            credits[key] = credits.get(key, 0) + credit
            
    elif model == "position_based":
        # 40% first, 40% last, 20% middle
        if len(touchpoints) == 1:
            tp = touchpoints[0]
            key = f"{tp['campaign']}_{tp['source']}_{tp['medium']}"
            credits[key] = total_value
        elif len(touchpoints) == 2:
            # 50/50 split
            for tp in touchpoints:
                key = f"{tp['campaign']}_{tp['source']}_{tp['medium']}"
                credits[key] = total_value / 2
        else:
            # First touch: 40%
            first = touchpoints[0]
            key = f"{first['campaign']}_{first['source']}_{first['medium']}"
            credits[key] = total_value * 0.4
            
            # Last touch: 40%
            last = touchpoints[-1]
            key = f"{last['campaign']}_{last['source']}_{last['medium']}"
            credits[key] = credits.get(key, 0) + (total_value * 0.4)
            
            # Middle touches: 20% distributed
            middle = touchpoints[1:-1]
            if middle:
                middle_credit = (total_value * 0.2) / len(middle)
                for tp in middle:
                    key = f"{tp['campaign']}_{tp['source']}_{tp['medium']}"
                    credits[key] = credits.get(key, 0) + middle_credit
    
    # Convert keys back to touchpoint format
    result = {}
    for key, value in credits.items():
        parts = key.split("_")
        result[key] = {
            "campaign": parts[0] if len(parts) > 0 else None,
            "source": parts[1] if len(parts) > 1 else None,
            "medium": parts[2] if len(parts) > 2 else None,
            "credit": value
        }
        
    return result

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
        
        # Calculate attribution breakdown
        if touchpoints:
            # Get attribution model
            model_name = frappe.db.get_single_value("TrackFlow Settings", "default_attribution_model") or "last_touch"
            attribution_credits = calculate_attribution_credits(touchpoints, model_name, deal.annual_revenue or 0)
            attribution_summary["attribution_breakdown"] = attribution_credits
        
        return attribution_summary
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Deal Attribution Report Error")
        return {"error": str(e)}
