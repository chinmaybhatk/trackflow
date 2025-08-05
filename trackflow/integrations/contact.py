# -*- coding: utf-8 -*-
# Copyright (c) 2024, TrackFlow and contributors
# For license information, please see license.txt

"""
TrackFlow Contact Integration

This module provides integration between TrackFlow and Frappe CRM Contacts.
"""

import frappe
from frappe import _
import json
from datetime import datetime


def on_contact_create(doc, method):
    """Hook called when a contact is created"""
    try:
        # Check if contact was created from a tracked link
        if hasattr(doc, '_trackflow_data'):
            trackflow_data = doc._trackflow_data
            
            # Create link between contact and tracked link
            create_contact_link_association(
                contact=doc.name,
                tracked_link=trackflow_data.get('tracked_link'),
                click_event=trackflow_data.get('click_event')
            )
            
            # Track conversion if specified
            if trackflow_data.get('track_conversion'):
                track_contact_conversion(
                    contact=doc.name,
                    tracked_link=trackflow_data.get('tracked_link')
                )
                
    except Exception as e:
        frappe.log_error(f"TrackFlow Contact Integration Error: {str(e)}", "on_contact_create")


def create_contact_link_association(contact, tracked_link, click_event=None):
    """Create association between contact and tracked link"""
    if not tracked_link:
        return
        
    # Check if association already exists
    existing = frappe.db.exists({
        'doctype': 'Contact Link Association',
        'contact': contact,
        'tracked_link': tracked_link
    })
    
    if not existing:
        frappe.get_doc({
            'doctype': 'Contact Link Association',
            'contact': contact,
            'tracked_link': tracked_link,
            'click_event': click_event,
            'association_date': datetime.now()
        }).insert(ignore_permissions=True)


def track_contact_conversion(contact, tracked_link):
    """Track contact creation as a conversion"""
    if not tracked_link:
        return
        
    # Get the campaign associated with the link
    campaign = frappe.db.get_value('Tracked Link', tracked_link, 'campaign')
    
    # Create conversion record
    conversion = frappe.get_doc({
        'doctype': 'Link Conversion',
        'tracked_link': tracked_link,
        'campaign': campaign,
        'conversion_type': 'Contact Created',
        'reference_doctype': 'Contact',
        'reference_name': contact,
        'conversion_date': datetime.now()
    })
    conversion.insert(ignore_permissions=True)


def get_contact_tracking_timeline(contact):
    """Get complete tracking timeline for a contact"""
    # Get all click events for this contact
    timeline = frappe.db.sql("""
        SELECT 
            ce.timestamp,
            ce.event_type,
            ce.page_url,
            ce.referrer,
            tl.short_code,
            tl.campaign_name,
            ce.session_id
        FROM `tabClick Event` ce
        JOIN `tabTracked Link` tl ON ce.tracked_link = tl.name
        WHERE ce.contact = %(contact)s
            OR ce.email = (SELECT email_id FROM `tabContact` WHERE name = %(contact)s LIMIT 1)
        ORDER BY ce.timestamp DESC
    """, {'contact': contact}, as_dict=True)
    
    # Group by session
    sessions = {}
    for event in timeline:
        session_id = event.get('session_id', 'unknown')
        if session_id not in sessions:
            sessions[session_id] = {
                'session_id': session_id,
                'start_time': event.timestamp,
                'end_time': event.timestamp,
                'events': []
            }
        sessions[session_id]['events'].append(event)
        sessions[session_id]['start_time'] = min(sessions[session_id]['start_time'], event.timestamp)
        sessions[session_id]['end_time'] = max(sessions[session_id]['end_time'], event.timestamp)
        
    return list(sessions.values())


@frappe.whitelist()
def get_contact_engagement_score(contact):
    """Calculate engagement score for a contact based on tracking data"""
    if not frappe.has_permission('Contact', 'read', contact):
        frappe.throw(_("Not permitted to view this contact"))
        
    # Define scoring weights
    weights = {
        'page_view': 1,
        'link_click': 2,
        'form_submit': 5,
        'conversion': 10,
        'email_open': 2,
        'email_click': 3
    }
    
    # Get all events
    events = frappe.db.sql("""
        SELECT 
            event_type,
            COUNT(*) as count
        FROM `tabClick Event`
        WHERE contact = %(contact)s
            OR email = (SELECT email_id FROM `tabContact` WHERE name = %(contact)s LIMIT 1)
        GROUP BY event_type
    """, {'contact': contact}, as_dict=True)
    
    # Calculate score
    total_score = 0
    breakdown = {}
    
    for event in events:
        event_type = event.event_type
        count = event.count
        weight = weights.get(event_type, 1)
        score = count * weight
        
        total_score += score
        breakdown[event_type] = {
            'count': count,
            'weight': weight,
            'score': score
        }
        
    # Get recency bonus
    last_activity = frappe.db.sql("""
        SELECT MAX(timestamp) as last_activity
        FROM `tabClick Event`
        WHERE contact = %(contact)s
            OR email = (SELECT email_id FROM `tabContact` WHERE name = %(contact)s LIMIT 1)
    """, {'contact': contact}, as_dict=True)[0]
    
    if last_activity and last_activity.last_activity:
        days_since_activity = (datetime.now() - last_activity.last_activity).days
        if days_since_activity < 7:
            recency_bonus = 10
        elif days_since_activity < 30:
            recency_bonus = 5
        elif days_since_activity < 90:
            recency_bonus = 2
        else:
            recency_bonus = 0
            
        total_score += recency_bonus
        breakdown['recency_bonus'] = recency_bonus
        
    return {
        'total_score': total_score,
        'breakdown': breakdown,
        'last_activity': last_activity.last_activity if last_activity else None,
        'engagement_level': get_engagement_level(total_score)
    }


def get_engagement_level(score):
    """Get engagement level based on score"""
    if score >= 100:
        return 'Very High'
    elif score >= 50:
        return 'High'
    elif score >= 20:
        return 'Medium'
    elif score >= 5:
        return 'Low'
    else:
        return 'Very Low'


@frappe.whitelist()
def send_tracked_email_to_contact(contact, email_template, campaign=None):
    """Send a tracked email to a contact"""
    if not frappe.has_permission('Contact', 'write', contact):
        frappe.throw(_("Not permitted to email this contact"))
        
    contact_doc = frappe.get_doc('Contact', contact)
    if not contact_doc.email_id:
        frappe.throw(_("Contact does not have an email address"))
        
    # Get email template
    template = frappe.get_doc('Email Template', email_template)
    
    # Generate tracked links for all links in the email
    from trackflow.utils.link_generator import generate_tracked_links_in_content
    
    tracked_content = generate_tracked_links_in_content(
        template.response_html or template.response,
        campaign=campaign or template.name,
        reference_doctype='Contact',
        reference_name=contact
    )
    
    # Send email
    frappe.sendmail(
        recipients=[contact_doc.email_id],
        subject=template.subject,
        message=tracked_content,
        reference_doctype='Contact',
        reference_name=contact,
        unsubscribe_message=_("Click here to unsubscribe")
    )
    
    # Log email sent
    frappe.get_doc({
        'doctype': 'Email Campaign Log',
        'contact': contact,
        'email_template': email_template,
        'campaign': campaign,
        'sent_on': datetime.now(),
        'status': 'Sent'
    }).insert(ignore_permissions=True)
    
    return {'status': 'success', 'message': 'Email sent successfully'}
