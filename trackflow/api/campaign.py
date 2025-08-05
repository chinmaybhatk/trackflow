# -*- coding: utf-8 -*-
# Copyright (c) 2024, TrackFlow and contributors
# For license information, please see license.txt

"""
Campaign API endpoints for TrackFlow
"""

import frappe
from frappe import _
import json
from datetime import datetime
from trackflow.utils.link_generator import generate_tracked_link, bulk_generate_links


@frappe.whitelist()
def create_campaign(data):
    """Create a new campaign"""
    
    if isinstance(data, str):
        data = json.loads(data)
        
    # Validate required fields
    if not data.get('campaign_name'):
        frappe.throw(_("Campaign name is required"))
        
    # Create campaign document
    campaign = frappe.get_doc({
        'doctype': 'Link Campaign',
        'campaign_name': data.get('campaign_name'),
        'description': data.get('description'),
        'campaign_type': data.get('campaign_type', 'General'),
        'status': 'Draft',
        'start_date': data.get('start_date') or datetime.now().date(),
        'end_date': data.get('end_date'),
        'budget': data.get('budget', 0),
        'target_audience': data.get('target_audience'),
        'objectives': data.get('objectives'),
        'utm_source': data.get('utm_source'),
        'utm_medium': data.get('utm_medium'),
        'utm_campaign': data.get('utm_campaign') or data.get('campaign_name').lower().replace(' ', '_')
    })
    
    # Add team members if provided
    if data.get('team_members'):
        for member in data.get('team_members'):
            campaign.append('team_members', {
                'user': member.get('user'),
                'role': member.get('role', 'Member')
            })
            
    campaign.insert()
    
    # Create initial links if provided
    if data.get('initial_links'):
        create_campaign_links(campaign.name, data.get('initial_links'))
        
    return {
        'campaign_id': campaign.name,
        'status': 'success',
        'message': f"Campaign '{campaign.campaign_name}' created successfully"
    }


@frappe.whitelist()
def update_campaign(campaign_id, data):
    """Update an existing campaign"""
    
    if isinstance(data, str):
        data = json.loads(data)
        
    # Get campaign
    campaign = frappe.get_doc('Link Campaign', campaign_id)
    
    # Check permissions
    if not campaign.has_permission('write'):
        frappe.throw(_("You don't have permission to update this campaign"))
        
    # Update fields
    updateable_fields = [
        'campaign_name', 'description', 'campaign_type', 'status',
        'end_date', 'budget', 'target_audience', 'objectives',
        'utm_source', 'utm_medium', 'utm_campaign'
    ]
    
    for field in updateable_fields:
        if field in data:
            setattr(campaign, field, data[field])
            
    campaign.save()
    
    return {
        'campaign_id': campaign.name,
        'status': 'success',
        'message': 'Campaign updated successfully'
    }


@frappe.whitelist()
def create_campaign_links(campaign_id, links_data):
    """Create multiple links for a campaign"""
    
    if isinstance(links_data, str):
        links_data = json.loads(links_data)
        
    # Get campaign
    campaign = frappe.get_doc('Link Campaign', campaign_id)
    
    # Prepare link data with campaign defaults
    for link in links_data:
        link['campaign'] = campaign_id
        link['campaign_name'] = campaign.campaign_name
        
        # Use campaign UTM defaults if not specified
        if not link.get('utm_source') and campaign.utm_source:
            link['utm_source'] = campaign.utm_source
        if not link.get('utm_medium') and campaign.utm_medium:
            link['utm_medium'] = campaign.utm_medium
        if not link.get('utm_campaign') and campaign.utm_campaign:
            link['utm_campaign'] = campaign.utm_campaign
            
    # Generate links
    results = bulk_generate_links(links_data)
    
    # Update campaign link count
    campaign.total_links = frappe.db.count('Tracked Link', {'campaign': campaign_id})
    campaign.save(ignore_permissions=True)
    
    return results


@frappe.whitelist()
def get_campaign_links(campaign_id, filters=None):
    """Get all links for a campaign"""
    
    if isinstance(filters, str):
        filters = json.loads(filters)
        
    filters = filters or {}
    filters['campaign'] = campaign_id
    
    links = frappe.get_all(
        'Tracked Link',
        filters=filters,
        fields=[
            'name', 'short_code', 'destination_url', 'clicks',
            'conversions', 'is_active', 'created', 'expires_on'
        ],
        order_by='created desc'
    )
    
    # Add full URLs
    domain = frappe.db.get_single_value('TrackFlow Settings', 'default_domain')
    protocol = 'https' if frappe.db.get_single_value('TrackFlow Settings', 'use_https') else 'http'
    
    for link in links:
        link['short_url'] = f"{protocol}://{domain}/r/{link.short_code}"
        
    return links


@frappe.whitelist()
def clone_campaign(campaign_id, new_name=None):
    """Clone an existing campaign"""
    
    # Get original campaign
    original = frappe.get_doc('Link Campaign', campaign_id)
    
    # Create new campaign
    new_campaign = frappe.copy_doc(original)
    new_campaign.campaign_name = new_name or f"{original.campaign_name} (Copy)"
    new_campaign.status = 'Draft'
    new_campaign.total_links = 0
    new_campaign.total_clicks = 0
    new_campaign.total_conversions = 0
    new_campaign.total_revenue = 0
    
    # Clear statistics
    new_campaign.statistics = []
    
    new_campaign.insert()
    
    # Clone links if requested
    if frappe.form_dict.get('clone_links'):
        clone_campaign_links(campaign_id, new_campaign.name)
        
    return {
        'campaign_id': new_campaign.name,
        'status': 'success',
        'message': f"Campaign cloned successfully as '{new_campaign.campaign_name}'"
    }


def clone_campaign_links(source_campaign, target_campaign):
    """Clone all links from source to target campaign"""
    
    # Get all links from source campaign
    links = frappe.get_all(
        'Tracked Link',
        filters={'campaign': source_campaign},
        fields=['*']
    )
    
    # Create new links
    for link in links:
        # Remove system fields
        for field in ['name', 'creation', 'modified', 'modified_by', 'owner', 'idx']:
            link.pop(field, None)
            
        # Reset statistics
        link['clicks'] = 0
        link['conversions'] = 0
        link['last_click'] = None
        link['last_conversion'] = None
        
        # Update campaign
        link['campaign'] = target_campaign
        
        # Generate new short code
        link['short_code'] = None
        
        # Create link
        generate_tracked_link(link)


@frappe.whitelist()
def pause_campaign(campaign_id):
    """Pause an active campaign"""
    
    campaign = frappe.get_doc('Link Campaign', campaign_id)
    
    if campaign.status != 'Active':
        frappe.throw(_("Only active campaigns can be paused"))
        
    campaign.status = 'Paused'
    campaign.save()
    
    # Deactivate all campaign links
    frappe.db.sql("""
        UPDATE `tabTracked Link`
        SET is_active = 0
        WHERE campaign = %(campaign)s
    """, {'campaign': campaign_id})
    
    return {
        'status': 'success',
        'message': 'Campaign paused successfully'
    }


@frappe.whitelist()
def resume_campaign(campaign_id):
    """Resume a paused campaign"""
    
    campaign = frappe.get_doc('Link Campaign', campaign_id)
    
    if campaign.status != 'Paused':
        frappe.throw(_("Only paused campaigns can be resumed"))
        
    campaign.status = 'Active'
    campaign.save()
    
    # Reactivate campaign links
    frappe.db.sql("""
        UPDATE `tabTracked Link`
        SET is_active = 1
        WHERE campaign = %(campaign)s
            AND (expires_on IS NULL OR expires_on > CURDATE())
    """, {'campaign': campaign_id})
    
    return {
        'status': 'success',
        'message': 'Campaign resumed successfully'
    }


@frappe.whitelist()
def complete_campaign(campaign_id):
    """Mark a campaign as completed"""
    
    campaign = frappe.get_doc('Link Campaign', campaign_id)
    
    if campaign.status == 'Completed':
        frappe.throw(_("Campaign is already completed"))
        
    campaign.status = 'Completed'
    campaign.actual_end_date = datetime.now().date()
    campaign.save()
    
    # Generate final report
    report = generate_campaign_report(campaign_id)
    
    return {
        'status': 'success',
        'message': 'Campaign marked as completed',
        'report_summary': report.get('summary')
    }


def generate_campaign_report(campaign_id):
    """Generate comprehensive campaign report"""
    
    from trackflow.api.analytics import get_campaign_performance
    
    # Get full performance data
    performance = get_campaign_performance(campaign_id)
    
    # Calculate additional metrics
    campaign = frappe.get_doc('Link Campaign', campaign_id)
    
    summary = {
        'campaign_name': campaign.campaign_name,
        'duration_days': (campaign.actual_end_date or campaign.end_date - campaign.start_date).days,
        'total_budget': campaign.budget,
        'total_spent': campaign.total_cost,
        'total_links': performance['total_links'],
        'total_clicks': performance['total_clicks'],
        'unique_visitors': performance['unique_visitors'],
        'total_conversions': sum(c['count'] for c in performance['conversions']),
        'total_revenue': sum(c['total_value'] for c in performance['conversions']),
        'roi': performance['roi'],
        'cost_per_click': campaign.total_cost / performance['total_clicks'] if performance['total_clicks'] > 0 else 0,
        'cost_per_conversion': campaign.total_cost / sum(c['count'] for c in performance['conversions']) if performance['conversions'] else 0
    }
    
    # Store report
    campaign.final_report = json.dumps({
        'summary': summary,
        'performance': performance,
        'generated_on': datetime.now().isoformat()
    })
    campaign.save(ignore_permissions=True)
    
    return {
        'summary': summary,
        'performance': performance
    }


@frappe.whitelist()
def get_campaign_templates():
    """Get campaign templates for quick setup"""
    
    templates = [
        {
            'name': 'Product Launch',
            'description': 'Template for new product launch campaigns',
            'campaign_type': 'Product Launch',
            'suggested_channels': ['email', 'social', 'paid'],
            'utm_defaults': {
                'utm_medium': 'launch',
                'utm_campaign': 'product_launch_{date}'
            },
            'duration_days': 30
        },
        {
            'name': 'Email Newsletter',
            'description': 'Template for email newsletter campaigns',
            'campaign_type': 'Email',
            'suggested_channels': ['email'],
            'utm_defaults': {
                'utm_source': 'newsletter',
                'utm_medium': 'email',
                'utm_campaign': 'newsletter_{date}'
            },
            'duration_days': 7
        },
        {
            'name': 'Social Media',
            'description': 'Template for social media campaigns',
            'campaign_type': 'Social',
            'suggested_channels': ['facebook', 'twitter', 'linkedin', 'instagram'],
            'utm_defaults': {
                'utm_medium': 'social',
                'utm_campaign': 'social_{platform}_{date}'
            },
            'duration_days': 14
        },
        {
            'name': 'Event Promotion',
            'description': 'Template for event promotion campaigns',
            'campaign_type': 'Event',
            'suggested_channels': ['email', 'social', 'paid', 'partner'],
            'utm_defaults': {
                'utm_medium': 'event',
                'utm_campaign': 'event_{name}_{date}'
            },
            'duration_days': 45
        },
        {
            'name': 'Content Marketing',
            'description': 'Template for content marketing campaigns',
            'campaign_type': 'Content',
            'suggested_channels': ['blog', 'social', 'email'],
            'utm_defaults': {
                'utm_medium': 'content',
                'utm_campaign': 'content_{topic}_{date}'
            },
            'duration_days': 60
        }
    ]
    
    return templates


@frappe.whitelist()
def apply_campaign_template(template_name, campaign_data):
    """Apply a template to create a campaign"""
    
    if isinstance(campaign_data, str):
        campaign_data = json.loads(campaign_data)
        
    # Get template
    templates = get_campaign_templates()
    template = next((t for t in templates if t['name'] == template_name), None)
    
    if not template:
        frappe.throw(_(f"Template '{template_name}' not found"))
        
    # Merge template with campaign data
    campaign_data['campaign_type'] = template['campaign_type']
    
    # Apply UTM defaults
    for key, value in template['utm_defaults'].items():
        if '{date}' in value:
            value = value.replace('{date}', datetime.now().strftime('%Y%m%d'))
        if '{platform}' in value and campaign_data.get('platform'):
            value = value.replace('{platform}', campaign_data['platform'])
        if '{name}' in value and campaign_data.get('event_name'):
            value = value.replace('{name}', campaign_data['event_name'].lower().replace(' ', '_'))
        if '{topic}' in value and campaign_data.get('topic'):
            value = value.replace('{topic}', campaign_data['topic'].lower().replace(' ', '_'))
            
        campaign_data[key] = value
        
    # Set duration if not specified
    if not campaign_data.get('end_date') and template.get('duration_days'):
        from datetime import timedelta
        campaign_data['end_date'] = (datetime.now() + timedelta(days=template['duration_days'])).date()
        
    # Create campaign
    return create_campaign(campaign_data)
