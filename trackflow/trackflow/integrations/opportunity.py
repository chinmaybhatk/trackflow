import frappe
from frappe import _

def on_opportunity_create(doc, method):
    """Handle opportunity creation - link to visitor and create attribution"""
    # Check if opportunity came from a tracked source
    if doc.source == "Campaign" or frappe.db.exists("Lead Link Association", {"lead": doc.party_name}):
        # Get visitor ID from lead association
        visitor_id = None
        campaign = None
        
        if doc.opportunity_from == "Lead":
            lead_association = frappe.db.get_value(
                "Lead Link Association",
                {"lead": doc.party_name},
                ["visitor_id", "campaign"],
                as_dict=1
            )
            
            if lead_association:
                visitor_id = lead_association.visitor_id
                campaign = lead_association.campaign
        
        # Create deal link association
        if visitor_id:
            deal_link = frappe.new_doc("Deal Link Association")
            deal_link.deal = doc.name
            deal_link.deal_name = doc.title
            deal_link.visitor_id = visitor_id
            deal_link.campaign = campaign or doc.campaign_name
            deal_link.lead = doc.party_name if doc.opportunity_from == "Lead" else None
            deal_link.insert(ignore_permissions=True)
        
        # Create deal attribution
        if campaign or doc.campaign_name:
            attribution = frappe.new_doc("Deal Attribution")
            attribution.deal = doc.name
            attribution.deal_name = doc.title
            attribution.campaign = campaign or doc.campaign_name
            attribution.deal_value = doc.opportunity_amount
            attribution.attribution_model = "Last Touch"  # Can be configured
            attribution.attribution_percentage = 100
            attribution.insert(ignore_permissions=True)
        
        # Create conversion record
        if visitor_id:
            conversion = frappe.new_doc("TrackFlow Conversion")
            conversion.visitor_id = visitor_id
            conversion.campaign = campaign or doc.campaign_name
            conversion.conversion_type = "Deal Created"
            conversion.conversion_date = frappe.utils.now()
            conversion.deal = doc.name
            conversion.deal_value = doc.opportunity_amount
            
            # Get session details
            session = frappe.db.get_value(
                "Visitor Session",
                {"visitor_id": visitor_id},
                ["utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term", "referrer"],
                as_dict=1,
                order_by="creation desc"
            )
            
            if session:
                conversion.update(session)
            
            conversion.insert(ignore_permissions=True)
            
            # Send notification
            from trackflow.trackflow.notifications import send_conversion_notification
            send_conversion_notification(conversion)

def on_opportunity_update(doc, method):
    """Handle opportunity updates - track stage changes and deal won"""
    if doc.has_value_changed("status"):
        # Create deal stage change record
        stage_change = frappe.new_doc("Deal Stage Change")
        stage_change.deal = doc.name
        stage_change.deal_name = doc.title
        stage_change.from_stage = doc.get_doc_before_save().status if doc.get_doc_before_save() else None
        stage_change.to_stage = doc.status
        stage_change.changed_on = frappe.utils.now()
        stage_change.changed_by = frappe.session.user
        
        # Get campaign from attribution
        campaign = frappe.db.get_value("Deal Attribution", {"deal": doc.name}, "campaign")
        if campaign:
            stage_change.campaign = campaign
        
        stage_change.insert(ignore_permissions=True)
        
        # If deal is won, create conversion
        if doc.status in ["Closed", "Converted", "Won"]:  # Configure based on your status
            # Get visitor ID from deal link
            deal_link = frappe.db.get_value(
                "Deal Link Association",
                {"deal": doc.name},
                ["visitor_id", "campaign"],
                as_dict=1
            )
            
            if deal_link and deal_link.visitor_id:
                # Check if conversion already exists
                existing = frappe.db.exists(
                    "TrackFlow Conversion",
                    {
                        "visitor_id": deal_link.visitor_id,
                        "conversion_type": "Deal Won",
                        "deal": doc.name
                    }
                )
                
                if not existing:
                    conversion = frappe.new_doc("TrackFlow Conversion")
                    conversion.visitor_id = deal_link.visitor_id
                    conversion.campaign = deal_link.campaign
                    conversion.conversion_type = "Deal Won"
                    conversion.conversion_date = frappe.utils.now()
                    conversion.deal = doc.name
                    conversion.deal_value = doc.opportunity_amount
                    conversion.insert(ignore_permissions=True)
                    
                    # Send notification
                    from trackflow.trackflow.notifications import send_conversion_notification
                    send_conversion_notification(conversion)
                    
                    # Update campaign goal progress
                    if deal_link.campaign:
                        from trackflow.trackflow.doctype.trackflow_campaign.trackflow_campaign import update_campaign_metrics
                        campaign_doc = frappe.get_doc("TrackFlow Campaign", deal_link.campaign)
                        update_campaign_metrics(campaign_doc)

def get_opportunity_source_options():
    """Get list of active campaigns for opportunity source"""
    campaigns = frappe.get_all(
        "TrackFlow Campaign",
        filters={"status": "Active"},
        fields=["name", "campaign_name"],
        order_by="creation desc"
    )
    
    return [{"value": c.name, "label": c.campaign_name} for c in campaigns]

def get_opportunity_metrics(opportunity_name):
    """Get tracking metrics for an opportunity"""
    metrics = {
        "visitor_sessions": 0,
        "page_views": 0,
        "time_to_convert": None,
        "attribution": None,
        "touchpoints": []
    }
    
    # Get deal link association
    deal_link = frappe.db.get_value(
        "Deal Link Association",
        {"deal": opportunity_name},
        ["visitor_id", "campaign", "lead"],
        as_dict=1
    )
    
    if not deal_link or not deal_link.visitor_id:
        return metrics
    
    # Get visitor sessions
    sessions = frappe.get_all(
        "Visitor Session",
        filters={"visitor_id": deal_link.visitor_id},
        fields=["name", "visit_date", "page_views", "session_duration", "utm_source", "utm_medium"]
    )
    
    metrics["visitor_sessions"] = len(sessions)
    metrics["page_views"] = sum(s.page_views for s in sessions)
    
    # Get attribution
    attribution = frappe.db.get_value(
        "Deal Attribution",
        {"deal": opportunity_name},
        ["campaign", "attribution_model", "attribution_percentage"],
        as_dict=1
    )
    
    if attribution:
        metrics["attribution"] = attribution
    
    # Get touchpoints
    touchpoints = []
    
    # Page views
    page_views = frappe.get_all(
        "Page View",
        filters={"visitor_id": deal_link.visitor_id},
        fields=["page_title", "page_url", "view_date"],
        order_by="view_date",
        limit=10
    )
    
    for pv in page_views:
        touchpoints.append({
            "type": "Page View",
            "title": pv.page_title,
            "url": pv.page_url,
            "date": pv.view_date
        })
    
    # Form submissions
    conversions = frappe.get_all(
        "TrackFlow Conversion",
        filters={
            "visitor_id": deal_link.visitor_id,
            "conversion_type": "Form Submission"
        },
        fields=["conversion_date", "form_id"],
        order_by="conversion_date"
    )
    
    for conv in conversions:
        touchpoints.append({
            "type": "Form Submission",
            "title": conv.form_id,
            "date": conv.conversion_date
        })
    
    # Sort touchpoints by date
    touchpoints.sort(key=lambda x: x["date"])
    metrics["touchpoints"] = touchpoints
    
    # Calculate time to convert
    if sessions and deal_link.lead:
        lead_creation = frappe.db.get_value("Lead", deal_link.lead, "creation")
        if lead_creation:
            first_visit = min(s.visit_date for s in sessions)
            time_diff = frappe.utils.date_diff(lead_creation, first_visit)
            metrics["time_to_convert"] = time_diff
    
    return metrics
