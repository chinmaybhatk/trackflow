"""
TrackFlow integration for CRM Lead DocType
"""

import frappe
from frappe import _
from trackflow.utils import get_visitor_from_request, create_visitor_session
from trackflow.attribution import AttributionCalculator
import json


def on_lead_create(doc, method):
    """
    Handle CRM Lead creation - Track source and attribution
    """
    try:
        # Check if this lead is being created from a web form or tracked source
        if frappe.local.request and hasattr(frappe.local, 'request_ip'):
            visitor = get_visitor_from_request()
            
            if visitor:
                # Update lead with tracking information
                doc.trackflow_visitor_id = visitor.name
                doc.trackflow_source = visitor.source
                doc.trackflow_medium = visitor.medium
                doc.trackflow_campaign = visitor.campaign
                doc.trackflow_first_touch_date = visitor.first_seen
                doc.trackflow_last_touch_date = visitor.last_seen
                doc.trackflow_touch_count = visitor.page_views
                
                # Save without triggering hooks again
                doc.db_update()
                
                # Link visitor to lead
                visitor.lead = doc.name
                visitor.save(ignore_permissions=True)
                
                # Create conversion event
                create_conversion_event(doc, visitor, "lead_created")
                
    except Exception as e:
        frappe.log_error(f"TrackFlow: Error in on_lead_create: {str(e)}")


def on_lead_update(doc, method):
    """
    Handle CRM Lead updates - Track status changes and engagement
    """
    try:
        # Check if status changed
        if doc.has_value_changed("status"):
            old_status = doc.get_doc_before_save().status if doc.get_doc_before_save() else None
            
            # Track status change event
            if doc.trackflow_visitor_id:
                visitor = frappe.get_doc("Visitor", doc.trackflow_visitor_id)
                
                event_data = {
                    "event_type": "lead_status_change",
                    "old_status": old_status,
                    "new_status": doc.status,
                    "lead": doc.name
                }
                
                create_tracking_event(visitor, event_data)
                
                # Update engagement score based on status
                update_engagement_score(doc, visitor)
                
    except Exception as e:
        frappe.log_error(f"TrackFlow: Error in on_lead_update: {str(e)}")


def on_lead_trash(doc, method):
    """
    Handle CRM Lead deletion - Clean up tracking data
    """
    try:
        if doc.trackflow_visitor_id:
            # Unlink visitor from lead
            visitor = frappe.get_doc("Visitor", doc.trackflow_visitor_id)
            visitor.lead = None
            visitor.save(ignore_permissions=True)
            
    except Exception as e:
        frappe.log_error(f"TrackFlow: Error in on_lead_trash: {str(e)}")


def create_conversion_event(lead, visitor, event_type):
    """
    Create a conversion event for tracking
    """
    event = frappe.new_doc("Visitor Event")
    event.visitor = visitor.name
    event.event_type = event_type
    event.event_category = "conversion"
    event.event_data = json.dumps({
        "lead": lead.name,
        "lead_name": lead.lead_name,
        "email": lead.email,
        "source": lead.trackflow_source,
        "campaign": lead.trackflow_campaign
    })
    event.timestamp = frappe.utils.now()
    event.insert(ignore_permissions=True)
    
    # Update campaign metrics if applicable
    if lead.trackflow_campaign:
        update_campaign_conversion(lead.trackflow_campaign, "lead")


def create_tracking_event(visitor, event_data):
    """
    Create a general tracking event
    """
    event = frappe.new_doc("Visitor Event")
    event.visitor = visitor.name
    event.event_type = event_data.get("event_type")
    event.event_category = "engagement"
    event.event_data = json.dumps(event_data)
    event.timestamp = frappe.utils.now()
    event.insert(ignore_permissions=True)


def update_engagement_score(lead, visitor):
    """
    Update engagement score based on lead status
    """
    # Define score weights for different statuses
    status_scores = {
        "Open": 10,
        "Replied": 20,
        "Interested": 50,
        "Converted": 100,
        "Do Not Contact": -50
    }
    
    current_score = visitor.engagement_score or 0
    status_score = status_scores.get(lead.status, 0)
    
    # Update visitor engagement score
    visitor.engagement_score = current_score + status_score
    visitor.last_activity = frappe.utils.now()
    visitor.save(ignore_permissions=True)


def update_campaign_conversion(campaign_name, conversion_type):
    """
    Update campaign conversion metrics
    """
    try:
        campaign = frappe.get_doc("Campaign", campaign_name)
        
        if conversion_type == "lead":
            campaign.leads_generated = (campaign.leads_generated or 0) + 1
            
        # Calculate conversion rate
        if campaign.total_clicks > 0:
            campaign.conversion_rate = (campaign.leads_generated / campaign.total_clicks) * 100
            
        campaign.save(ignore_permissions=True)
        
    except Exception as e:
        frappe.log_error(f"TrackFlow: Error updating campaign conversion: {str(e)}")


def get_lead_source_data(lead_name):
    """
    Get tracking source data for a lead
    """
    lead = frappe.get_doc("CRM Lead", lead_name)
    
    data = {
        "source": lead.trackflow_source,
        "medium": lead.trackflow_medium,
        "campaign": lead.trackflow_campaign,
        "first_touch": lead.trackflow_first_touch_date,
        "last_touch": lead.trackflow_last_touch_date,
        "touch_count": lead.trackflow_touch_count,
        "visitor_id": lead.trackflow_visitor_id
    }
    
    # Get visitor journey if available
    if lead.trackflow_visitor_id:
        visitor = frappe.get_doc("Visitor", lead.trackflow_visitor_id)
        data["visitor_journey"] = get_visitor_journey(visitor)
        
    return data


def get_visitor_journey(visitor):
    """
    Get the complete journey of a visitor
    """
    events = frappe.get_all(
        "Visitor Event",
        filters={"visitor": visitor.name},
        fields=["event_type", "event_data", "timestamp"],
        order_by="timestamp asc"
    )
    
    journey = []
    for event in events:
        journey.append({
            "timestamp": event.timestamp,
            "type": event.event_type,
            "data": json.loads(event.event_data) if event.event_data else {}
        })
        
    return journey
