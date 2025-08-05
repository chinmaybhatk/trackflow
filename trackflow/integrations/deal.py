# -*- coding: utf-8 -*-
# Copyright (c) 2024, TrackFlow and contributors
# For license information, please see license.txt

"""
TrackFlow Deal Integration

This module provides integration between TrackFlow and CRM Deals/Opportunities.
"""

import frappe
from frappe import _
import json
from datetime import datetime


def on_deal_create(doc, method):
    """Hook called when a deal/opportunity is created"""
    try:
        # Check if deal was influenced by tracked links
        if hasattr(doc, '_trackflow_data'):
            trackflow_data = doc._trackflow_data
            
            # Create deal attribution
            create_deal_attribution(
                deal=doc.name,
                tracked_link=trackflow_data.get('tracked_link'),
                attribution_data=trackflow_data
            )
            
        # Check for related lead/contact with tracking
        elif doc.get('party_name'):
            inherit_tracking_from_party(doc)
            
    except Exception as e:
        frappe.log_error(f"TrackFlow Deal Integration Error: {str(e)}", "on_deal_create")


def on_deal_update(doc, method):
    """Hook called when a deal is updated"""
    try:
        # Track stage changes
        if doc.has_value_changed('sales_stage'):
            track_deal_stage_change(
                deal=doc.name,
                old_stage=doc.get_doc_before_save().sales_stage,
                new_stage=doc.sales_stage,
                deal_value=doc.get('opportunity_amount', 0)
            )
            
        # Track closure
        if doc.status == 'Closed' and doc.has_value_changed('status'):
            track_deal_closure(doc)
            
    except Exception as e:
        frappe.log_error(f"TrackFlow Deal Integration Error: {str(e)}", "on_deal_update")


def create_deal_attribution(deal, tracked_link, attribution_data):
    """Create attribution record for a deal"""
    # Get all touchpoints that led to this deal
    touchpoints = get_deal_touchpoints(deal, attribution_data)
    
    # Get attribution model
    attribution_model = frappe.get_doc(
        'Attribution Model',
        frappe.db.get_single_value('TrackFlow Settings', 'default_attribution_model')
    )
    
    # Calculate attribution
    deal_value = frappe.db.get_value('Opportunity', deal, 'opportunity_amount') or 0
    attribution = attribution_model.calculate_attribution(touchpoints, deal_value)
    
    # Create attribution records
    for channel, data in attribution.items():
        frappe.get_doc({
            'doctype': 'Deal Attribution',
            'deal': deal,
            'channel': channel,
            'attribution_credit': data['credit'],
            'attributed_value': data['value'],
            'touchpoint_count': len(data.get('touchpoint_ids', [])),
            'attribution_model': attribution_model.name,
            'calculation_date': datetime.now()
        }).insert(ignore_permissions=True)


def inherit_tracking_from_party(doc):
    """Inherit tracking data from related lead or contact"""
    party_type = doc.get('opportunity_from')
    party_name = doc.get('party_name')
    
    if not party_type or not party_name:
        return
        
    # Get tracking data from party
    if party_type == 'Lead':
        associations = frappe.get_all(
            'Lead Link Association',
            filters={'lead': party_name},
            fields=['tracked_link', 'click_event']
        )
    elif party_type == 'Customer':
        # Get primary contact
        contact = frappe.db.get_value(
            'Dynamic Link',
            {
                'link_doctype': 'Customer',
                'link_name': party_name,
                'parenttype': 'Contact'
            },
            'parent'
        )
        
        if contact:
            associations = frappe.get_all(
                'Contact Link Association',
                filters={'contact': contact},
                fields=['tracked_link', 'click_event']
            )
        else:
            associations = []
    else:
        associations = []
        
    # Create deal associations
    for assoc in associations:
        frappe.get_doc({
            'doctype': 'Deal Link Association',
            'deal': doc.name,
            'tracked_link': assoc.tracked_link,
            'click_event': assoc.click_event,
            'inherited_from': f"{party_type}:{party_name}",
            'association_date': datetime.now()
        }).insert(ignore_permissions=True)


def get_deal_touchpoints(deal, attribution_data=None):
    """Get all touchpoints that influenced a deal"""
    # Get direct associations
    direct_touchpoints = frappe.db.sql("""
        SELECT 
            ce.timestamp,
            ce.channel,
            ce.source,
            ce.medium,
            ce.campaign,
            tl.name as tracked_link
        FROM `tabClick Event` ce
        JOIN `tabTracked Link` tl ON ce.tracked_link = tl.name
        JOIN `tabDeal Link Association` dla ON dla.tracked_link = tl.name
        WHERE dla.deal = %(deal)s
        ORDER BY ce.timestamp
    """, {'deal': deal}, as_dict=True)
    
    # Get inherited touchpoints from lead/contact
    inherited_touchpoints = frappe.db.sql("""
        SELECT 
            ce.timestamp,
            ce.channel,
            ce.source,
            ce.medium,
            ce.campaign,
            tl.name as tracked_link
        FROM `tabClick Event` ce
        JOIN `tabTracked Link` tl ON ce.tracked_link = tl.name
        JOIN `tabDeal Link Association` dla ON dla.tracked_link = tl.name
        WHERE dla.deal = %(deal)s
            AND dla.inherited_from IS NOT NULL
        ORDER BY ce.timestamp
    """, {'deal': deal}, as_dict=True)
    
    # Combine and deduplicate
    all_touchpoints = direct_touchpoints + inherited_touchpoints
    seen = set()
    unique_touchpoints = []
    
    for tp in all_touchpoints:
        key = (tp['tracked_link'], tp['timestamp'])
        if key not in seen:
            seen.add(key)
            unique_touchpoints.append(tp)
            
    return unique_touchpoints


def track_deal_stage_change(deal, old_stage, new_stage, deal_value):
    """Track deal stage progression"""
    # Create stage change record
    frappe.get_doc({
        'doctype': 'Deal Stage Change',
        'deal': deal,
        'old_stage': old_stage,
        'new_stage': new_stage,
        'deal_value': deal_value,
        'change_date': datetime.now()
    }).insert(ignore_permissions=True)
    
    # Update campaign performance if moving to won stage
    if is_won_stage(new_stage) and not is_won_stage(old_stage):
        update_campaign_performance_for_deal(deal, deal_value)


def track_deal_closure(doc):
    """Track deal closure and final attribution"""
    is_won = doc.get('status') == 'Closed' and doc.get('opportunity_amount', 0) > 0
    
    # Get all associated campaigns
    campaigns = frappe.db.sql("""
        SELECT DISTINCT tl.campaign
        FROM `tabTracked Link` tl
        JOIN `tabDeal Link Association` dla ON dla.tracked_link = tl.name
        WHERE dla.deal = %(deal)s
            AND tl.campaign IS NOT NULL
    """, {'deal': doc.name}, as_dict=True)
    
    for campaign in campaigns:
        # Create final conversion record
        frappe.get_doc({
            'doctype': 'Link Conversion',
            'campaign': campaign.campaign,
            'conversion_type': 'Deal Won' if is_won else 'Deal Lost',
            'conversion_value': doc.get('opportunity_amount', 0) if is_won else 0,
            'reference_doctype': 'Opportunity',
            'reference_name': doc.name,
            'conversion_date': datetime.now(),
            'is_final_conversion': 1
        }).insert(ignore_permissions=True)


def is_won_stage(stage):
    """Check if a stage is considered 'won'"""
    won_stages = frappe.db.get_single_value('CRM Settings', 'won_stages') or 'Closed-Won,Won'
    return stage in won_stages.split(',')


def update_campaign_performance_for_deal(deal, deal_value):
    """Update campaign performance metrics for a won deal"""
    # Get attribution data
    attributions = frappe.get_all(
        'Deal Attribution',
        filters={'deal': deal},
        fields=['channel', 'attributed_value', 'attribution_credit']
    )
    
    # Update campaign metrics
    for attr in attributions:
        campaigns = frappe.db.sql("""
            SELECT DISTINCT lc.name as campaign
            FROM `tabLink Campaign` lc
            JOIN `tabTracked Link` tl ON tl.campaign = lc.name
            JOIN `tabClick Event` ce ON ce.tracked_link = tl.name
            WHERE ce.channel = %(channel)s
        """, {'channel': attr.channel}, as_dict=True)
        
        for campaign in campaigns:
            # Update campaign revenue
            campaign_doc = frappe.get_doc('Link Campaign', campaign.campaign)
            campaign_doc.total_revenue = (campaign_doc.total_revenue or 0) + attr.attributed_value
            campaign_doc.total_conversions = (campaign_doc.total_conversions or 0) + attr.attribution_credit
            campaign_doc.save(ignore_permissions=True)


@frappe.whitelist()
def get_deal_attribution_report(deal):
    """Get detailed attribution report for a deal"""
    if not frappe.has_permission('Opportunity', 'read', deal):
        frappe.throw(_("Not permitted to view this deal"))
        
    # Get deal info
    deal_doc = frappe.get_doc('Opportunity', deal)
    
    # Get touchpoints
    touchpoints = get_deal_touchpoints(deal)
    
    # Get attribution
    attributions = frappe.get_all(
        'Deal Attribution',
        filters={'deal': deal},
        fields=['*']
    )
    
    # Get timeline
    timeline = frappe.db.sql("""
        SELECT 
            ce.timestamp,
            ce.event_type,
            ce.page_url,
            tl.campaign_name,
            ce.channel,
            ce.source,
            ce.medium
        FROM `tabClick Event` ce
        JOIN `tabTracked Link` tl ON ce.tracked_link = tl.name
        JOIN `tabDeal Link Association` dla ON dla.tracked_link = tl.name
        WHERE dla.deal = %(deal)s
        ORDER BY ce.timestamp
    """, {'deal': deal}, as_dict=True)
    
    return {
        'deal': {
            'name': deal_doc.name,
            'title': deal_doc.title or deal_doc.party_name,
            'value': deal_doc.opportunity_amount,
            'stage': deal_doc.sales_stage,
            'status': deal_doc.status
        },
        'touchpoints': touchpoints,
        'attribution': attributions,
        'timeline': timeline,
        'summary': {
            'total_touchpoints': len(touchpoints),
            'channels_involved': len(set(tp['channel'] for tp in touchpoints if tp.get('channel'))),
            'days_to_close': (deal_doc.closing_date - deal_doc.transaction_date).days if deal_doc.closing_date else None
        }
    }
