# -*- coding: utf-8 -*-
# Copyright (c) 2024, TrackFlow and contributors
# For license information, please see license.txt

"""
TrackFlow Lead Integration

This module provides integration between TrackFlow and Frappe CRM Leads.
"""

import frappe
from frappe import _
import json
from datetime import datetime


def on_lead_create(doc, method):
    """Hook called when a lead is created"""
    try:
        # Check if lead was created from a tracked link
        if hasattr(doc, '_trackflow_data'):
            trackflow_data = doc._trackflow_data
            
            # Create link between lead and tracked link
            create_lead_link_association(
                lead=doc.name,
                tracked_link=trackflow_data.get('tracked_link'),
                click_event=trackflow_data.get('click_event')
            )
            
            # Update conversion tracking
            if trackflow_data.get('track_conversion'):
                track_lead_conversion(
                    lead=doc.name,
                    tracked_link=trackflow_data.get('tracked_link'),
                    conversion_value=doc.get('expected_value', 0)
                )
                
    except Exception as e:
        frappe.log_error(f"TrackFlow Lead Integration Error: {str(e)}", "on_lead_create")


def on_lead_update(doc, method):
    """Hook called when a lead is updated"""
    try:
        # Track status changes
        if doc.has_value_changed('status'):
            track_lead_status_change(
                lead=doc.name,
                old_status=doc.get_doc_before_save().status,
                new_status=doc.status
            )
            
        # Track conversion if lead is converted
        if doc.status == 'Converted' and doc.has_value_changed('status'):
            track_lead_final_conversion(doc)
            
    except Exception as e:
        frappe.log_error(f"TrackFlow Lead Integration Error: {str(e)}", "on_lead_update")


def create_lead_link_association(lead, tracked_link, click_event=None):
    """Create association between lead and tracked link"""
    if not tracked_link:
        return
        
    # Check if association already exists
    existing = frappe.db.exists({
        'doctype': 'Lead Link Association',
        'lead': lead,
        'tracked_link': tracked_link
    })
    
    if not existing:
        frappe.get_doc({
            'doctype': 'Lead Link Association',
            'lead': lead,
            'tracked_link': tracked_link,
            'click_event': click_event,
            'association_date': datetime.now()
        }).insert(ignore_permissions=True)


def track_lead_conversion(lead, tracked_link, conversion_value=0):
    """Track lead creation as a conversion"""
    if not tracked_link:
        return
        
    # Get the campaign associated with the link
    campaign = frappe.db.get_value('Tracked Link', tracked_link, 'campaign')
    
    # Create conversion record
    conversion = frappe.get_doc({
        'doctype': 'Link Conversion',
        'tracked_link': tracked_link,
        'campaign': campaign,
        'conversion_type': 'Lead Created',
        'conversion_value': conversion_value,
        'reference_doctype': 'Lead',
        'reference_name': lead,
        'conversion_date': datetime.now()
    })
    conversion.insert(ignore_permissions=True)
    
    # Update link statistics
    frappe.db.set_value('Tracked Link', tracked_link, {
        'conversions': frappe.db.get_value('Tracked Link', tracked_link, 'conversions') + 1,
        'last_conversion': datetime.now()
    })


def track_lead_status_change(lead, old_status, new_status):
    """Track lead status changes"""
    # Get associated tracked links
    associations = frappe.get_all(
        'Lead Link Association',
        filters={'lead': lead},
        fields=['tracked_link', 'click_event']
    )
    
    for assoc in associations:
        # Log status change event
        frappe.get_doc({
            'doctype': 'Lead Status Change',
            'lead': lead,
            'tracked_link': assoc.tracked_link,
            'old_status': old_status,
            'new_status': new_status,
            'change_date': datetime.now()
        }).insert(ignore_permissions=True)


def track_lead_final_conversion(doc):
    """Track final lead conversion to customer"""
    # Get all associated tracked links
    associations = frappe.get_all(
        'Lead Link Association',
        filters={'lead': doc.name},
        fields=['tracked_link', 'click_event']
    )
    
    for assoc in associations:
        # Create final conversion record
        frappe.get_doc({
            'doctype': 'Link Conversion',
            'tracked_link': assoc.tracked_link,
            'conversion_type': 'Lead Converted',
            'conversion_value': doc.get('expected_value', 0),
            'reference_doctype': 'Lead',
            'reference_name': doc.name,
            'conversion_date': datetime.now(),
            'is_final_conversion': 1
        }).insert(ignore_permissions=True)


def get_lead_attribution_data(lead):
    """Get attribution data for a lead"""
    # Get all touchpoints for the lead
    touchpoints = frappe.db.sql("""
        SELECT 
            ce.timestamp,
            ce.channel,
            ce.source,
            ce.medium,
            ce.campaign,
            tl.name as tracked_link,
            tl.campaign_name
        FROM `tabClick Event` ce
        JOIN `tabTracked Link` tl ON ce.tracked_link = tl.name
        JOIN `tabLead Link Association` lla ON lla.tracked_link = tl.name
        WHERE lla.lead = %(lead)s
        ORDER BY ce.timestamp
    """, {'lead': lead}, as_dict=True)
    
    # Get attribution model
    attribution_model = frappe.get_doc(
        'Attribution Model',
        frappe.db.get_single_value('TrackFlow Settings', 'default_attribution_model')
    )
    
    # Calculate attribution
    attribution = attribution_model.calculate_attribution(
        touchpoints,
        conversion_value=frappe.db.get_value('Lead', lead, 'expected_value')
    )
    
    return {
        'touchpoints': touchpoints,
        'attribution': attribution,
        'model': attribution_model.name
    }


@frappe.whitelist()
def get_lead_tracking_info(lead):
    """Get tracking information for a lead (for UI display)"""
    if not frappe.has_permission('Lead', 'read', lead):
        frappe.throw(_("Not permitted to view this lead"))
        
    # Get associated links
    links = frappe.db.sql("""
        SELECT 
            lla.tracked_link,
            lla.click_event,
            lla.association_date,
            tl.short_code,
            tl.destination_url,
            tl.campaign_name,
            ce.timestamp as click_time,
            ce.ip_address,
            ce.country,
            ce.city
        FROM `tabLead Link Association` lla
        JOIN `tabTracked Link` tl ON lla.tracked_link = tl.name
        LEFT JOIN `tabClick Event` ce ON lla.click_event = ce.name
        WHERE lla.lead = %(lead)s
        ORDER BY lla.association_date DESC
    """, {'lead': lead}, as_dict=True)
    
    # Get conversions
    conversions = frappe.get_all(
        'Link Conversion',
        filters={
            'reference_doctype': 'Lead',
            'reference_name': lead
        },
        fields=['*']
    )
    
    # Get attribution data
    attribution = get_lead_attribution_data(lead)
    
    return {
        'links': links,
        'conversions': conversions,
        'attribution': attribution
    }


@frappe.whitelist()
def generate_lead_tracked_link(lead, campaign=None, custom_params=None):
    """Generate a tracked link for a lead"""
    if not frappe.has_permission('Lead', 'write', lead):
        frappe.throw(_("Not permitted to modify this lead"))
        
    lead_doc = frappe.get_doc('Lead', lead)
    
    # Prepare link data
    link_data = {
        'destination_url': frappe.db.get_single_value('TrackFlow Settings', 'lead_form_url') or '/lead-form',
        'campaign': campaign or 'lead-followup',
        'campaign_name': f"Lead Follow-up - {lead_doc.lead_name}",
        'utm_source': 'email',
        'utm_medium': 'lead-nurture',
        'utm_campaign': campaign or 'lead-followup',
        'reference_doctype': 'Lead',
        'reference_name': lead
    }
    
    # Add custom parameters if provided
    if custom_params:
        link_data.update(json.loads(custom_params) if isinstance(custom_params, str) else custom_params)
        
    # Create tracked link
    tracked_link = frappe.get_doc({
        'doctype': 'Tracked Link',
        **link_data
    })
    tracked_link.insert()
    
    return {
        'tracked_link': tracked_link.name,
        'short_url': tracked_link.get_short_url(),
        'qr_code': tracked_link.generate_qr_code()
    }
