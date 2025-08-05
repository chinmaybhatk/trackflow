# -*- coding: utf-8 -*-
# Copyright (c) 2024, chinmaybhatk and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import cint

@frappe.whitelist()
def create_link(campaign, custom_identifier=None, target_url=None, tags=None, expiry_date=None):
    """Create a new tracking link via API"""
    # Check API permissions
    if not frappe.has_permission("Tracked Link", "create"):
        frappe.throw(_("Not permitted"), frappe.PermissionError)
        
    # Import the function from tracked_link doctype
    from trackflow.trackflow.doctype.tracked_link.tracked_link import create_tracking_link
    
    return create_tracking_link(
        campaign=campaign,
        custom_identifier=custom_identifier,
        target_url=target_url,
        tags=tags,
        expiry_date=expiry_date
    )

@frappe.whitelist()
def get_analytics(campaign=None, link=None, period=30, group_by="day"):
    """Get analytics data via API"""
    # Check permissions
    if campaign and not frappe.has_permission("Link Campaign", "read", campaign):
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    if link and not frappe.has_permission("Tracked Link", "read", link):
        frappe.throw(_("Not permitted"), frappe.PermissionError)
        
    period = cint(period)
    
    # Build query conditions
    conditions = []
    if campaign:
        conditions.append(f"ce.campaign = '{campaign}'")
    if link:
        conditions.append(f"ce.tracked_link = '{link}'")
        
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    # Get analytics data based on grouping
    if group_by == "day":
        data = frappe.db.sql(f"""
            SELECT 
                DATE(ce.click_timestamp) as date,
                COUNT(*) as clicks,
                COUNT(DISTINCT ce.visitor_id) as unique_visitors
            FROM `tabClick Event` ce
            WHERE {where_clause}
            AND ce.click_timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
            GROUP BY DATE(ce.click_timestamp)
            ORDER BY date
        """, period, as_dict=True)
        
    elif group_by == "hour":
        data = frappe.db.sql(f"""
            SELECT 
                DATE_FORMAT(ce.click_timestamp, '%%Y-%%m-%%d %%H:00:00') as hour,
                COUNT(*) as clicks,
                COUNT(DISTINCT ce.visitor_id) as unique_visitors
            FROM `tabClick Event` ce
            WHERE {where_clause}
            AND ce.click_timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
            GROUP BY DATE_FORMAT(ce.click_timestamp, '%%Y-%%m-%%d %%H:00:00')
            ORDER BY hour
        """, period, as_dict=True)
        
    elif group_by == "device":
        data = frappe.db.sql(f"""
            SELECT 
                ce.device_type as device,
                COUNT(*) as clicks,
                COUNT(DISTINCT ce.visitor_id) as unique_visitors
            FROM `tabClick Event` ce
            WHERE {where_clause}
            AND ce.click_timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
            GROUP BY ce.device_type
        """, period, as_dict=True)
        
    elif group_by == "country":
        data = frappe.db.sql(f"""
            SELECT 
                ce.country,
                COUNT(*) as clicks,
                COUNT(DISTINCT ce.visitor_id) as unique_visitors
            FROM `tabClick Event` ce
            WHERE {where_clause}
            AND ce.click_timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
            AND ce.country IS NOT NULL
            GROUP BY ce.country
            ORDER BY clicks DESC
        """, period, as_dict=True)
        
    else:
        # Default summary
        data = frappe.db.sql(f"""
            SELECT 
                COUNT(*) as total_clicks,
                COUNT(DISTINCT ce.visitor_id) as unique_visitors,
                COUNT(DISTINCT ce.campaign) as campaigns,
                COUNT(DISTINCT ce.tracked_link) as links
            FROM `tabClick Event` ce
            WHERE {where_clause}
            AND ce.click_timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
        """, period, as_dict=True)[0]
        
    return data

@frappe.whitelist()
def track_conversion(visitor_id, conversion_type, conversion_value=0, link=None, campaign=None):
    """Track a conversion event via API"""
    # Find the most recent click from this visitor
    filters = {"visitor_id": visitor_id}
    if link:
        filters["tracked_link"] = link
    if campaign:
        filters["campaign"] = campaign
        
    click_event = frappe.get_list("Click Event",
        filters=filters,
        fields=["name", "tracked_link", "campaign"],
        order_by="click_timestamp desc",
        limit=1
    )
    
    if not click_event:
        frappe.throw(_("No click event found for this visitor"))
        
    click = click_event[0]
    
    # Create conversion record
    conversion = frappe.new_doc("Link Conversion")
    conversion.click_event = click.name
    conversion.tracked_link = click.tracked_link
    conversion.campaign = click.campaign
    conversion.visitor_id = visitor_id
    conversion.conversion_type = conversion_type
    conversion.conversion_value = conversion_value
    conversion.insert(ignore_permissions=True)
    
    # Update click event
    frappe.db.set_value("Click Event", click.name, {
        "led_to_conversion": 1,
        "conversion_type": conversion_type,
        "conversion_value": conversion_value
    })
    
    return {
        "conversion_id": conversion.name,
        "click_event": click.name,
        "campaign": click.campaign,
        "tracked_link": click.tracked_link
    }
