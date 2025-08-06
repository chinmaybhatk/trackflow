"""
TrackFlow integration for CRM Deal DocType
"""

import frappe
from frappe import _
from trackflow.attribution import AttributionCalculator
import json


def after_insert(doc, method):
    """
    Handle CRM Deal creation - Initialize attribution tracking
    """
    try:
        # Check if deal is linked to a lead with tracking data
        if doc.lead:
            lead = frappe.get_doc("CRM Lead", doc.lead)
            
            if lead.trackflow_visitor_id:
                # Copy tracking data from lead
                doc.trackflow_first_touch_source = lead.trackflow_source
                doc.trackflow_last_touch_source = lead.trackflow_source
                doc.trackflow_marketing_influenced = 1 if lead.trackflow_campaign else 0
                
                # Set default attribution model
                doc.trackflow_attribution_model = frappe.db.get_single_value(
                    "TrackFlow Settings", 
                    "default_attribution_model"
                ) or "last_touch"
                
                # Save without triggering hooks again
                doc.db_update()
                
                # Create deal creation event
                create_deal_event(doc, lead.trackflow_visitor_id, "deal_created")
                
    except Exception as e:
        frappe.log_error(f"TrackFlow: Error in CRM Deal after_insert: {str(e)}")


def on_update(doc, method):
    """
    Handle CRM Deal updates - Track stage changes and value updates
    """
    try:
        # Check if stage or value changed
        if doc.has_value_changed("stage") or doc.has_value_changed("annual_revenue"):
            old_doc = doc.get_doc_before_save() if doc.get_doc_before_save() else None
            
            # Get visitor ID from linked lead
            visitor_id = get_visitor_from_deal(doc)
            
            if visitor_id:
                event_data = {
                    "event_type": "deal_updated",
                    "deal": doc.name,
                    "changes": {}
                }
                
                if doc.has_value_changed("stage"):
                    event_data["changes"]["stage"] = {
                        "old": old_doc.stage if old_doc else None,
                        "new": doc.stage
                    }
                    
                if doc.has_value_changed("annual_revenue"):
                    event_data["changes"]["annual_revenue"] = {
                        "old": old_doc.annual_revenue if old_doc else 0,
                        "new": doc.annual_revenue
                    }
                    
                create_deal_event(doc, visitor_id, "deal_updated", event_data)
                
                # Update campaign ROI if deal value changed
                if doc.has_value_changed("annual_revenue") and doc.trackflow_marketing_influenced:
                    update_campaign_roi(doc)
                    
    except Exception as e:
        frappe.log_error(f"TrackFlow: Error in CRM Deal on_update: {str(e)}")


def calculate_attribution(doc, method):
    """
    Calculate multi-touch attribution for closed deals
    """
    try:
        # Only calculate for won deals
        if doc.stage != "Won":
            return
            
        visitor_id = get_visitor_from_deal(doc)
        if not visitor_id:
            return
            
        # Initialize attribution calculator
        calculator = AttributionCalculator(
            visitor_id=visitor_id,
            conversion_value=doc.annual_revenue or 0,
            attribution_model=doc.trackflow_attribution_model or "last_touch"
        )
        
        # Calculate attribution
        attribution_result = calculator.calculate()
        
        # Store attribution data
        doc.trackflow_attribution_data = json.dumps(attribution_result)
        doc.db_update()
        
        # Update touchpoint credits
        update_touchpoint_credits(attribution_result, doc.annual_revenue)
        
        # Create conversion event
        create_deal_event(doc, visitor_id, "deal_won", {
            "value": doc.annual_revenue,
            "attribution": attribution_result
        })
        
        # Update campaign ROI
        update_campaign_roi_from_attribution(attribution_result, doc.annual_revenue)
        
    except Exception as e:
        frappe.log_error(f"TrackFlow: Error calculating attribution: {str(e)}")


def get_visitor_from_deal(deal):
    """
    Get visitor ID from deal's linked lead
    """
    if deal.lead:
        lead = frappe.get_value("CRM Lead", deal.lead, "trackflow_visitor_id")
        return lead
    return None


def create_deal_event(deal, visitor_id, event_type, additional_data=None):
    """
    Create a deal-related tracking event
    """
    event = frappe.new_doc("Visitor Event")
    event.visitor = visitor_id
    event.event_type = event_type
    event.event_category = "deal"
    
    event_data = {
        "deal": deal.name,
        "deal_name": deal.deal_name,
        "stage": deal.stage,
        "value": deal.annual_revenue
    }
    
    if additional_data:
        event_data.update(additional_data)
        
    event.event_data = json.dumps(event_data)
    event.timestamp = frappe.utils.now()
    event.insert(ignore_permissions=True)


def update_touchpoint_credits(attribution_result, deal_value):
    """
    Update touchpoint records with attribution credits
    """
    for touchpoint in attribution_result.get("touchpoints", []):
        try:
            # Create attribution record
            attr_record = frappe.new_doc("Attribution Record")
            attr_record.touchpoint_type = touchpoint.get("type")
            attr_record.touchpoint_id = touchpoint.get("id")
            attr_record.source = touchpoint.get("source")
            attr_record.medium = touchpoint.get("medium")
            attr_record.campaign = touchpoint.get("campaign")
            attr_record.credit_percentage = touchpoint.get("credit", 0)
            attr_record.credit_value = (touchpoint.get("credit", 0) / 100) * deal_value
            attr_record.deal = touchpoint.get("deal")
            attr_record.timestamp = touchpoint.get("timestamp")
            attr_record.insert(ignore_permissions=True)
            
        except Exception as e:
            frappe.log_error(f"Error updating touchpoint credit: {str(e)}")


def update_campaign_roi(deal):
    """
    Update campaign ROI based on deal value
    """
    try:
        # Get campaign from lead
        if deal.lead:
            campaign_name = frappe.get_value("CRM Lead", deal.lead, "trackflow_campaign")
            
            if campaign_name:
                campaign = frappe.get_doc("Campaign", campaign_name)
                
                # Update revenue
                campaign.revenue_generated = (campaign.revenue_generated or 0) + (deal.annual_revenue or 0)
                
                # Calculate ROI
                if campaign.total_cost > 0:
                    campaign.roi = ((campaign.revenue_generated - campaign.total_cost) / campaign.total_cost) * 100
                    
                campaign.save(ignore_permissions=True)
                
    except Exception as e:
        frappe.log_error(f"TrackFlow: Error updating campaign ROI: {str(e)}")


def update_campaign_roi_from_attribution(attribution_result, deal_value):
    """
    Update campaign ROI based on multi-touch attribution
    """
    try:
        # Group credits by campaign
        campaign_credits = {}
        
        for touchpoint in attribution_result.get("touchpoints", []):
            campaign = touchpoint.get("campaign")
            if campaign:
                credit_value = (touchpoint.get("credit", 0) / 100) * deal_value
                
                if campaign in campaign_credits:
                    campaign_credits[campaign] += credit_value
                else:
                    campaign_credits[campaign] = credit_value
                    
        # Update each campaign
        for campaign_name, credited_revenue in campaign_credits.items():
            try:
                campaign = frappe.get_doc("Campaign", campaign_name)
                campaign.attributed_revenue = (campaign.attributed_revenue or 0) + credited_revenue
                
                # Recalculate ROI with attributed revenue
                if campaign.total_cost > 0:
                    campaign.attributed_roi = ((campaign.attributed_revenue - campaign.total_cost) / campaign.total_cost) * 100
                    
                campaign.save(ignore_permissions=True)
                
            except Exception as e:
                frappe.log_error(f"Error updating campaign {campaign_name}: {str(e)}")
                
    except Exception as e:
        frappe.log_error(f"TrackFlow: Error updating campaign ROI from attribution: {str(e)}")


def get_deal_attribution_report(deal_name):
    """
    Get detailed attribution report for a deal
    """
    deal = frappe.get_doc("CRM Deal", deal_name)
    
    report = {
        "deal": deal_name,
        "value": deal.annual_revenue,
        "attribution_model": deal.trackflow_attribution_model,
        "first_touch_source": deal.trackflow_first_touch_source,
        "last_touch_source": deal.trackflow_last_touch_source,
        "marketing_influenced": deal.trackflow_marketing_influenced
    }
    
    # Parse attribution data if available
    if deal.trackflow_attribution_data:
        report["attribution_details"] = json.loads(deal.trackflow_attribution_data)
        
    # Get all touchpoints
    visitor_id = get_visitor_from_deal(deal)
    if visitor_id:
        touchpoints = frappe.get_all(
            "Visitor Event",
            filters={
                "visitor": visitor_id,
                "event_category": ["in", ["page_view", "conversion", "engagement"]]
            },
            fields=["event_type", "event_data", "timestamp"],
            order_by="timestamp asc"
        )
        
        report["customer_journey"] = touchpoints
        
    return report
