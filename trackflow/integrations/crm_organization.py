"""
TrackFlow integration for CRM Organization DocType
"""

import frappe
from frappe import _
from trackflow.utils import get_visitor_from_request
import json


def after_insert(doc, method):
    """
    Handle CRM Organization creation - Link tracking data if available
    """
    try:
        # Check if organization is being created from a tracked source
        if frappe.local.request and hasattr(frappe.local, 'request_ip'):
            visitor = get_visitor_from_request()
            
            if visitor:
                # Update organization with tracking information
                doc.trackflow_visitor_id = visitor.name
                doc.trackflow_last_campaign = visitor.campaign
                doc.trackflow_engagement_score = visitor.engagement_score or 0
                
                # Save without triggering hooks again
                doc.db_update()
                
                # Link visitor to organization
                visitor.organization = doc.name
                visitor.save(ignore_permissions=True)
                
                # Create organization creation event
                create_organization_event(doc, visitor, "organization_created")
                
        # Check if organization has associated leads
        link_organization_to_leads(doc)
        
    except Exception as e:
        frappe.log_error(f"TrackFlow: Error in CRM Organization after_insert: {str(e)}")


def on_update(doc, method):
    """
    Handle CRM Organization updates - Track engagement and activity
    """
    try:
        # Update engagement score from associated contacts and deals
        update_organization_engagement(doc)
        
        # Track significant changes
        if doc.has_value_changed("website") or doc.has_value_changed("industry"):
            if doc.trackflow_visitor_id:
                visitor = frappe.get_doc("Visitor", doc.trackflow_visitor_id)
                
                event_data = {
                    "event_type": "organization_updated",
                    "organization": doc.name,
                    "changes": {}
                }
                
                if doc.has_value_changed("website"):
                    event_data["changes"]["website"] = doc.website
                    
                if doc.has_value_changed("industry"):
                    event_data["changes"]["industry"] = doc.industry
                    
                create_organization_event(doc, visitor, "organization_updated", event_data)
                
    except Exception as e:
        frappe.log_error(f"TrackFlow: Error in CRM Organization on_update: {str(e)}")


def link_organization_to_leads(organization):
    """
    Link organization to leads with matching domain
    """
    try:
        if organization.website:
            # Extract domain from website
            domain = extract_domain(organization.website)
            
            if domain:
                # Find leads with matching email domain
                leads = frappe.get_all(
                    "CRM Lead",
                    filters=[["email", "like", f"%@{domain}"]],
                    fields=["name", "trackflow_visitor_id", "trackflow_campaign"]
                )
                
                for lead in leads:
                    # Update lead with organization
                    frappe.db.set_value("CRM Lead", lead.name, "organization", organization.name)
                    
                    # Aggregate tracking data
                    if lead.trackflow_visitor_id and not organization.trackflow_visitor_id:
                        organization.trackflow_visitor_id = lead.trackflow_visitor_id
                        organization.trackflow_last_campaign = lead.trackflow_campaign
                        organization.db_update()
                        
    except Exception as e:
        frappe.log_error(f"TrackFlow: Error linking organization to leads: {str(e)}")


def update_organization_engagement(organization):
    """
    Calculate and update organization engagement score
    """
    try:
        engagement_score = 0
        
        # Get all leads for this organization
        leads = frappe.get_all(
            "CRM Lead",
            filters={"organization": organization.name},
            fields=["status", "trackflow_touch_count"]
        )
        
        # Score based on lead activity
        lead_score = 0
        for lead in leads:
            if lead.status == "Open":
                lead_score += 10
            elif lead.status == "Replied":
                lead_score += 20
            elif lead.status == "Interested":
                lead_score += 50
                
            # Add touch count
            lead_score += (lead.trackflow_touch_count or 0) * 2
            
        engagement_score += lead_score
        
        # Get all deals for this organization
        deals = frappe.get_all(
            "CRM Deal",
            filters={"organization": organization.name},
            fields=["stage", "annual_revenue"]
        )
        
        # Score based on deal activity
        deal_score = 0
        for deal in deals:
            if deal.stage == "Qualification":
                deal_score += 30
            elif deal.stage == "Proposal":
                deal_score += 60
            elif deal.stage == "Negotiation":
                deal_score += 80
            elif deal.stage == "Won":
                deal_score += 100
                
        engagement_score += deal_score
        
        # Get recent visitor activity if linked
        if organization.trackflow_visitor_id:
            visitor = frappe.get_doc("Visitor", organization.trackflow_visitor_id)
            
            # Add visitor engagement score
            engagement_score += visitor.engagement_score or 0
            
            # Bonus for recent activity
            last_activity = visitor.last_seen
            if last_activity:
                days_since_activity = frappe.utils.date_diff(
                    frappe.utils.today(), 
                    frappe.utils.get_datetime(last_activity).date()
                )
                
                if days_since_activity <= 7:
                    engagement_score += 20
                elif days_since_activity <= 30:
                    engagement_score += 10
                    
        # Update organization
        organization.trackflow_engagement_score = engagement_score
        organization.db_update()
        
    except Exception as e:
        frappe.log_error(f"TrackFlow: Error updating organization engagement: {str(e)}")


def create_organization_event(organization, visitor, event_type, additional_data=None):
    """
    Create an organization-related tracking event
    """
    event = frappe.new_doc("Visitor Event")
    event.visitor = visitor.name
    event.event_type = event_type
    event.event_category = "organization"
    
    event_data = {
        "organization": organization.name,
        "organization_name": organization.organization_name,
        "website": organization.website,
        "industry": organization.industry
    }
    
    if additional_data:
        event_data.update(additional_data)
        
    event.event_data = json.dumps(event_data)
    event.timestamp = frappe.utils.now()
    event.insert(ignore_permissions=True)


def extract_domain(website):
    """
    Extract domain from website URL
    """
    import re
    
    # Remove protocol
    domain = re.sub(r'^https?://', '', website)
    
    # Remove www
    domain = re.sub(r'^www\.', '', domain)
    
    # Remove path
    domain = domain.split('/')[0]
    
    # Remove port
    domain = domain.split(':')[0]
    
    return domain.lower()


def get_organization_tracking_summary(organization_name):
    """
    Get comprehensive tracking summary for an organization
    """
    organization = frappe.get_doc("CRM Organization", organization_name)
    
    summary = {
        "organization": organization_name,
        "engagement_score": organization.trackflow_engagement_score,
        "last_campaign": organization.trackflow_last_campaign,
        "visitor_id": organization.trackflow_visitor_id
    }
    
    # Get associated leads
    leads = frappe.get_all(
        "CRM Lead",
        filters={"organization": organization_name},
        fields=["name", "lead_name", "status", "trackflow_source", "trackflow_campaign"]
    )
    summary["leads"] = leads
    summary["total_leads"] = len(leads)
    
    # Get associated deals
    deals = frappe.get_all(
        "CRM Deal",
        filters={"organization": organization_name},
        fields=["name", "deal_name", "stage", "annual_revenue", "trackflow_attribution_model"]
    )
    summary["deals"] = deals
    summary["total_deals"] = len(deals)
    summary["total_deal_value"] = sum(d.annual_revenue or 0 for d in deals)
    
    # Get visitor journey if available
    if organization.trackflow_visitor_id:
        visitor = frappe.get_doc("Visitor", organization.trackflow_visitor_id)
        
        # Get recent events
        events = frappe.get_all(
            "Visitor Event",
            filters={"visitor": visitor.name},
            fields=["event_type", "event_category", "timestamp"],
            order_by="timestamp desc",
            limit=10
        )
        
        summary["recent_activity"] = events
        summary["first_seen"] = visitor.first_seen
        summary["last_seen"] = visitor.last_seen
        summary["total_page_views"] = visitor.page_views
        
    # Get campaign influence
    campaigns = {}
    for lead in leads:
        if lead.trackflow_campaign:
            if lead.trackflow_campaign in campaigns:
                campaigns[lead.trackflow_campaign] += 1
            else:
                campaigns[lead.trackflow_campaign] = 1
                
    summary["campaign_influence"] = campaigns
    
    return summary


def merge_organization_tracking(primary_org, duplicate_org):
    """
    Merge tracking data when organizations are merged
    """
    try:
        primary = frappe.get_doc("CRM Organization", primary_org)
        duplicate = frappe.get_doc("CRM Organization", duplicate_org)
        
        # Merge engagement scores
        primary.trackflow_engagement_score = (
            (primary.trackflow_engagement_score or 0) + 
            (duplicate.trackflow_engagement_score or 0)
        )
        
        # Keep the most recent campaign
        if duplicate.trackflow_last_campaign:
            primary.trackflow_last_campaign = duplicate.trackflow_last_campaign
            
        # Merge visitor IDs if different
        if duplicate.trackflow_visitor_id and duplicate.trackflow_visitor_id != primary.trackflow_visitor_id:
            # Create a note about the merge
            frappe.msgprint(
                f"Organization {duplicate_org} had different tracking data. "
                f"Manual review may be needed for visitor ID: {duplicate.trackflow_visitor_id}"
            )
            
        primary.save()
        
    except Exception as e:
        frappe.log_error(f"TrackFlow: Error merging organization tracking: {str(e)}")
