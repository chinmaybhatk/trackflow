# -*- coding: utf-8 -*-
# Copyright (c) 2024, TrackFlow and contributors
# For license information, please see license.txt

"""
Analytics API endpoints for TrackFlow
"""

import frappe
from frappe import _
from datetime import datetime, timedelta
import json
from frappe.utils import getdate, get_datetime, nowdate


@frappe.whitelist()
def get_dashboard_stats(filters=None):
    """Get dashboard statistics"""
    
    if isinstance(filters, str):
        filters = json.loads(filters)
    
    filters = filters or {}
    
    # Date range
    date_range = filters.get('date_range', 'last_30_days')
    start_date, end_date = get_date_range(date_range)
    
    # Get stats
    stats = {
        'total_links': get_total_links(start_date, end_date),
        'total_clicks': get_total_clicks(start_date, end_date),
        'total_conversions': get_total_conversions(start_date, end_date),
        'conversion_rate': 0,
        'top_campaigns': get_top_campaigns(start_date, end_date, limit=5),
        'top_links': get_top_links(start_date, end_date, limit=5),
        'click_timeline': get_click_timeline(start_date, end_date),
        'device_stats': get_device_stats(start_date, end_date),
        'location_stats': get_location_stats(start_date, end_date)
    }
    
    # Calculate conversion rate
    if stats['total_clicks'] > 0:
        stats['conversion_rate'] = (stats['total_conversions'] / stats['total_clicks']) * 100
        
    return stats


def get_date_range(range_type):
    """Get start and end date based on range type"""
    
    end_date = getdate(nowdate())
    
    if range_type == 'today':
        start_date = end_date
    elif range_type == 'yesterday':
        start_date = end_date - timedelta(days=1)
        end_date = start_date
    elif range_type == 'last_7_days':
        start_date = end_date - timedelta(days=7)
    elif range_type == 'last_30_days':
        start_date = end_date - timedelta(days=30)
    elif range_type == 'last_90_days':
        start_date = end_date - timedelta(days=90)
    elif range_type == 'this_month':
        start_date = end_date.replace(day=1)
    elif range_type == 'last_month':
        start_date = (end_date.replace(day=1) - timedelta(days=1)).replace(day=1)
        end_date = end_date.replace(day=1) - timedelta(days=1)
    else:
        # Custom range or default
        start_date = end_date - timedelta(days=30)
        
    return start_date, end_date


def get_total_links(start_date, end_date):
    """Get total number of links created"""
    
    return frappe.db.count('Tracked Link', {
        'creation': ('between', [start_date, end_date])
    })


def get_total_clicks(start_date, end_date):
    """Get total number of clicks"""
    
    return frappe.db.count('Click Event', {
        'timestamp': ('between', [start_date, end_date])
    })


def get_total_conversions(start_date, end_date):
    """Get total number of conversions"""
    
    return frappe.db.count('Link Conversion', {
        'conversion_date': ('between', [start_date, end_date])
    })


def get_top_campaigns(start_date, end_date, limit=5):
    """Get top performing campaigns"""
    
    campaigns = frappe.db.sql("""
        SELECT 
            lc.name,
            lc.campaign_name,
            COUNT(DISTINCT tl.name) as link_count,
            COUNT(ce.name) as click_count,
            COUNT(DISTINCT ce.visitor_id) as unique_visitors,
            COUNT(conv.name) as conversion_count,
            COALESCE(SUM(conv.conversion_value), 0) as total_value
        FROM `tabLink Campaign` lc
        LEFT JOIN `tabTracked Link` tl ON tl.campaign = lc.name
        LEFT JOIN `tabClick Event` ce ON ce.tracked_link = tl.name
            AND ce.timestamp BETWEEN %(start_date)s AND %(end_date)s
        LEFT JOIN `tabLink Conversion` conv ON conv.tracked_link = tl.name
            AND conv.conversion_date BETWEEN %(start_date)s AND %(end_date)s
        WHERE lc.creation BETWEEN %(start_date)s AND %(end_date)s
            OR ce.name IS NOT NULL
            OR conv.name IS NOT NULL
        GROUP BY lc.name
        ORDER BY click_count DESC
        LIMIT %(limit)s
    """, {
        'start_date': start_date,
        'end_date': end_date,
        'limit': limit
    }, as_dict=True)
    
    return campaigns


def get_top_links(start_date, end_date, limit=5):
    """Get top performing links"""
    
    links = frappe.db.sql("""
        SELECT 
            tl.name,
            tl.short_code,
            tl.destination_url,
            tl.campaign_name,
            COUNT(ce.name) as click_count,
            COUNT(DISTINCT ce.visitor_id) as unique_visitors,
            COUNT(conv.name) as conversion_count
        FROM `tabTracked Link` tl
        LEFT JOIN `tabClick Event` ce ON ce.tracked_link = tl.name
            AND ce.timestamp BETWEEN %(start_date)s AND %(end_date)s
        LEFT JOIN `tabLink Conversion` conv ON conv.tracked_link = tl.name
            AND conv.conversion_date BETWEEN %(start_date)s AND %(end_date)s
        WHERE tl.is_active = 1
        GROUP BY tl.name
        ORDER BY click_count DESC
        LIMIT %(limit)s
    """, {
        'start_date': start_date,
        'end_date': end_date,
        'limit': limit
    }, as_dict=True)
    
    return links


def get_click_timeline(start_date, end_date):
    """Get click timeline data"""
    
    # Determine grouping based on date range
    days_diff = (end_date - start_date).days
    
    if days_diff <= 1:
        # Group by hour
        timeline = frappe.db.sql("""
            SELECT 
                DATE_FORMAT(timestamp, '%%Y-%%m-%%d %%H:00:00') as period,
                COUNT(*) as clicks,
                COUNT(DISTINCT visitor_id) as unique_visitors
            FROM `tabClick Event`
            WHERE timestamp BETWEEN %(start_date)s AND %(end_date)s
            GROUP BY period
            ORDER BY period
        """, {
            'start_date': start_date,
            'end_date': end_date
        }, as_dict=True)
    elif days_diff <= 30:
        # Group by day
        timeline = frappe.db.sql("""
            SELECT 
                DATE(timestamp) as period,
                COUNT(*) as clicks,
                COUNT(DISTINCT visitor_id) as unique_visitors
            FROM `tabClick Event`
            WHERE timestamp BETWEEN %(start_date)s AND %(end_date)s
            GROUP BY period
            ORDER BY period
        """, {
            'start_date': start_date,
            'end_date': end_date
        }, as_dict=True)
    else:
        # Group by week
        timeline = frappe.db.sql("""
            SELECT 
                DATE_SUB(DATE(timestamp), INTERVAL WEEKDAY(timestamp) DAY) as period,
                COUNT(*) as clicks,
                COUNT(DISTINCT visitor_id) as unique_visitors
            FROM `tabClick Event`
            WHERE timestamp BETWEEN %(start_date)s AND %(end_date)s
            GROUP BY period
            ORDER BY period
        """, {
            'start_date': start_date,
            'end_date': end_date
        }, as_dict=True)
        
    return timeline


def get_device_stats(start_date, end_date):
    """Get device statistics"""
    
    devices = frappe.db.sql("""
        SELECT 
            device_type,
            COUNT(*) as count,
            COUNT(DISTINCT visitor_id) as unique_visitors
        FROM `tabClick Event`
        WHERE timestamp BETWEEN %(start_date)s AND %(end_date)s
            AND device_type IS NOT NULL
        GROUP BY device_type
        ORDER BY count DESC
    """, {
        'start_date': start_date,
        'end_date': end_date
    }, as_dict=True)
    
    return devices


def get_location_stats(start_date, end_date):
    """Get location statistics"""
    
    locations = frappe.db.sql("""
        SELECT 
            country,
            COUNT(*) as count,
            COUNT(DISTINCT visitor_id) as unique_visitors
        FROM `tabClick Event`
        WHERE timestamp BETWEEN %(start_date)s AND %(end_date)s
            AND country IS NOT NULL
        GROUP BY country
        ORDER BY count DESC
        LIMIT 10
    """, {
        'start_date': start_date,
        'end_date': end_date
    }, as_dict=True)
    
    return locations


@frappe.whitelist()
def get_link_analytics(tracked_link, filters=None):
    """Get detailed analytics for a specific link"""
    
    if isinstance(filters, str):
        filters = json.loads(filters)
        
    filters = filters or {}
    
    # Date range
    date_range = filters.get('date_range', 'last_30_days')
    start_date, end_date = get_date_range(date_range)
    
    # Get link details
    link = frappe.get_doc('Tracked Link', tracked_link)
    
    # Get analytics
    analytics = {
        'link_details': {
            'short_code': link.short_code,
            'destination_url': link.destination_url,
            'campaign': link.campaign,
            'created': link.creation
        },
        'total_clicks': get_link_clicks(tracked_link, start_date, end_date),
        'unique_visitors': get_link_unique_visitors(tracked_link, start_date, end_date),
        'conversions': get_link_conversions(tracked_link, start_date, end_date),
        'click_timeline': get_link_click_timeline(tracked_link, start_date, end_date),
        'referrers': get_link_referrers(tracked_link, start_date, end_date),
        'devices': get_link_devices(tracked_link, start_date, end_date),
        'locations': get_link_locations(tracked_link, start_date, end_date),
        'utm_performance': get_link_utm_performance(tracked_link, start_date, end_date)
    }
    
    return analytics


def get_link_clicks(tracked_link, start_date, end_date):
    """Get total clicks for a link"""
    
    return frappe.db.count('Click Event', {
        'tracked_link': tracked_link,
        'timestamp': ('between', [start_date, end_date])
    })


def get_link_unique_visitors(tracked_link, start_date, end_date):
    """Get unique visitors for a link"""
    
    result = frappe.db.sql("""
        SELECT COUNT(DISTINCT visitor_id) as count
        FROM `tabClick Event`
        WHERE tracked_link = %(tracked_link)s
            AND timestamp BETWEEN %(start_date)s AND %(end_date)s
    """, {
        'tracked_link': tracked_link,
        'start_date': start_date,
        'end_date': end_date
    }, as_dict=True)
    
    return result[0].count if result else 0


def get_link_conversions(tracked_link, start_date, end_date):
    """Get conversions for a link"""
    
    conversions = frappe.db.sql("""
        SELECT 
            conversion_type,
            COUNT(*) as count,
            SUM(conversion_value) as total_value
        FROM `tabLink Conversion`
        WHERE tracked_link = %(tracked_link)s
            AND conversion_date BETWEEN %(start_date)s AND %(end_date)s
        GROUP BY conversion_type
    """, {
        'tracked_link': tracked_link,
        'start_date': start_date,
        'end_date': end_date
    }, as_dict=True)
    
    return conversions


def get_link_click_timeline(tracked_link, start_date, end_date):
    """Get click timeline for a specific link"""
    
    days_diff = (end_date - start_date).days
    
    if days_diff <= 7:
        # Group by hour
        timeline = frappe.db.sql("""
            SELECT 
                DATE_FORMAT(timestamp, '%%Y-%%m-%%d %%H:00:00') as period,
                COUNT(*) as clicks
            FROM `tabClick Event`
            WHERE tracked_link = %(tracked_link)s
                AND timestamp BETWEEN %(start_date)s AND %(end_date)s
            GROUP BY period
            ORDER BY period
        """, {
            'tracked_link': tracked_link,
            'start_date': start_date,
            'end_date': end_date
        }, as_dict=True)
    else:
        # Group by day
        timeline = frappe.db.sql("""
            SELECT 
                DATE(timestamp) as period,
                COUNT(*) as clicks
            FROM `tabClick Event`
            WHERE tracked_link = %(tracked_link)s
                AND timestamp BETWEEN %(start_date)s AND %(end_date)s
            GROUP BY period
            ORDER BY period
        """, {
            'tracked_link': tracked_link,
            'start_date': start_date,
            'end_date': end_date
        }, as_dict=True)
        
    return timeline


def get_link_referrers(tracked_link, start_date, end_date):
    """Get referrer statistics for a link"""
    
    referrers = frappe.db.sql("""
        SELECT 
            referrer,
            COUNT(*) as count
        FROM `tabClick Event`
        WHERE tracked_link = %(tracked_link)s
            AND timestamp BETWEEN %(start_date)s AND %(end_date)s
            AND referrer IS NOT NULL
            AND referrer != ''
        GROUP BY referrer
        ORDER BY count DESC
        LIMIT 10
    """, {
        'tracked_link': tracked_link,
        'start_date': start_date,
        'end_date': end_date
    }, as_dict=True)
    
    return referrers


def get_link_devices(tracked_link, start_date, end_date):
    """Get device statistics for a link"""
    
    devices = frappe.db.sql("""
        SELECT 
            device_type,
            browser,
            os,
            COUNT(*) as count
        FROM `tabClick Event`
        WHERE tracked_link = %(tracked_link)s
            AND timestamp BETWEEN %(start_date)s AND %(end_date)s
        GROUP BY device_type, browser, os
        ORDER BY count DESC
    """, {
        'tracked_link': tracked_link,
        'start_date': start_date,
        'end_date': end_date
    }, as_dict=True)
    
    return devices


def get_link_locations(tracked_link, start_date, end_date):
    """Get location statistics for a link"""
    
    locations = frappe.db.sql("""
        SELECT 
            country,
            city,
            COUNT(*) as count
        FROM `tabClick Event`
        WHERE tracked_link = %(tracked_link)s
            AND timestamp BETWEEN %(start_date)s AND %(end_date)s
            AND country IS NOT NULL
        GROUP BY country, city
        ORDER BY count DESC
        LIMIT 20
    """, {
        'tracked_link': tracked_link,
        'start_date': start_date,
        'end_date': end_date
    }, as_dict=True)
    
    return locations


def get_link_utm_performance(tracked_link, start_date, end_date):
    """Get UTM parameter performance for a link"""
    
    utm_stats = frappe.db.sql("""
        SELECT 
            source,
            medium,
            campaign,
            COUNT(*) as clicks,
            COUNT(DISTINCT visitor_id) as unique_visitors
        FROM `tabClick Event`
        WHERE tracked_link = %(tracked_link)s
            AND timestamp BETWEEN %(start_date)s AND %(end_date)s
        GROUP BY source, medium, campaign
        ORDER BY clicks DESC
    """, {
        'tracked_link': tracked_link,
        'start_date': start_date,
        'end_date': end_date
    }, as_dict=True)
    
    return utm_stats


@frappe.whitelist()
def get_campaign_performance(campaign_id, filters=None):
    """Get performance metrics for a campaign"""
    
    if isinstance(filters, str):
        filters = json.loads(filters)
        
    filters = filters or {}
    
    # Date range
    date_range = filters.get('date_range', 'last_30_days')
    start_date, end_date = get_date_range(date_range)
    
    # Get campaign
    campaign = frappe.get_doc('Link Campaign', campaign_id)
    
    # Get metrics
    metrics = {
        'campaign_details': {
            'name': campaign.name,
            'campaign_name': campaign.campaign_name,
            'status': campaign.status,
            'start_date': campaign.start_date,
            'end_date': campaign.end_date
        },
        'total_links': get_campaign_links(campaign_id),
        'total_clicks': get_campaign_clicks(campaign_id, start_date, end_date),
        'unique_visitors': get_campaign_unique_visitors(campaign_id, start_date, end_date),
        'conversions': get_campaign_conversions(campaign_id, start_date, end_date),
        'roi': calculate_campaign_roi(campaign_id, start_date, end_date),
        'link_performance': get_campaign_link_performance(campaign_id, start_date, end_date),
        'channel_performance': get_campaign_channel_performance(campaign_id, start_date, end_date),
        'timeline': get_campaign_timeline(campaign_id, start_date, end_date)
    }
    
    return metrics


def get_campaign_links(campaign_id):
    """Get total links in a campaign"""
    
    return frappe.db.count('Tracked Link', {'campaign': campaign_id})


def get_campaign_clicks(campaign_id, start_date, end_date):
    """Get total clicks for a campaign"""
    
    result = frappe.db.sql("""
        SELECT COUNT(ce.name) as count
        FROM `tabClick Event` ce
        JOIN `tabTracked Link` tl ON ce.tracked_link = tl.name
        WHERE tl.campaign = %(campaign_id)s
            AND ce.timestamp BETWEEN %(start_date)s AND %(end_date)s
    """, {
        'campaign_id': campaign_id,
        'start_date': start_date,
        'end_date': end_date
    }, as_dict=True)
    
    return result[0].count if result else 0


def get_campaign_unique_visitors(campaign_id, start_date, end_date):
    """Get unique visitors for a campaign"""
    
    result = frappe.db.sql("""
        SELECT COUNT(DISTINCT ce.visitor_id) as count
        FROM `tabClick Event` ce
        JOIN `tabTracked Link` tl ON ce.tracked_link = tl.name
        WHERE tl.campaign = %(campaign_id)s
            AND ce.timestamp BETWEEN %(start_date)s AND %(end_date)s
    """, {
        'campaign_id': campaign_id,
        'start_date': start_date,
        'end_date': end_date
    }, as_dict=True)
    
    return result[0].count if result else 0


def get_campaign_conversions(campaign_id, start_date, end_date):
    """Get conversions for a campaign"""
    
    conversions = frappe.db.sql("""
        SELECT 
            conv.conversion_type,
            COUNT(conv.name) as count,
            SUM(conv.conversion_value) as total_value
        FROM `tabLink Conversion` conv
        JOIN `tabTracked Link` tl ON conv.tracked_link = tl.name
        WHERE tl.campaign = %(campaign_id)s
            AND conv.conversion_date BETWEEN %(start_date)s AND %(end_date)s
        GROUP BY conv.conversion_type
    """, {
        'campaign_id': campaign_id,
        'start_date': start_date,
        'end_date': end_date
    }, as_dict=True)
    
    return conversions


def calculate_campaign_roi(campaign_id, start_date, end_date):
    """Calculate ROI for a campaign"""
    
    # Get campaign cost
    campaign = frappe.get_doc('Link Campaign', campaign_id)
    cost = campaign.total_cost or 0
    
    # Get revenue
    revenue_result = frappe.db.sql("""
        SELECT SUM(conv.conversion_value) as total_revenue
        FROM `tabLink Conversion` conv
        JOIN `tabTracked Link` tl ON conv.tracked_link = tl.name
        WHERE tl.campaign = %(campaign_id)s
            AND conv.conversion_date BETWEEN %(start_date)s AND %(end_date)s
    """, {
        'campaign_id': campaign_id,
        'start_date': start_date,
        'end_date': end_date
    }, as_dict=True)
    
    revenue = revenue_result[0].total_revenue if revenue_result else 0
    
    # Calculate ROI
    if cost > 0:
        roi = ((revenue - cost) / cost) * 100
    else:
        roi = 0
        
    return {
        'cost': cost,
        'revenue': revenue,
        'profit': revenue - cost,
        'roi_percentage': roi
    }


def get_campaign_link_performance(campaign_id, start_date, end_date):
    """Get performance of individual links in a campaign"""
    
    links = frappe.db.sql("""
        SELECT 
            tl.name,
            tl.short_code,
            tl.destination_url,
            COUNT(ce.name) as clicks,
            COUNT(DISTINCT ce.visitor_id) as unique_visitors,
            COUNT(conv.name) as conversions,
            COALESCE(SUM(conv.conversion_value), 0) as conversion_value
        FROM `tabTracked Link` tl
        LEFT JOIN `tabClick Event` ce ON ce.tracked_link = tl.name
            AND ce.timestamp BETWEEN %(start_date)s AND %(end_date)s
        LEFT JOIN `tabLink Conversion` conv ON conv.tracked_link = tl.name
            AND conv.conversion_date BETWEEN %(start_date)s AND %(end_date)s
        WHERE tl.campaign = %(campaign_id)s
        GROUP BY tl.name
        ORDER BY clicks DESC
    """, {
        'campaign_id': campaign_id,
        'start_date': start_date,
        'end_date': end_date
    }, as_dict=True)
    
    return links


def get_campaign_channel_performance(campaign_id, start_date, end_date):
    """Get performance by channel for a campaign"""
    
    channels = frappe.db.sql("""
        SELECT 
            ce.channel,
            COUNT(ce.name) as clicks,
            COUNT(DISTINCT ce.visitor_id) as unique_visitors,
            COUNT(conv.name) as conversions,
            COALESCE(SUM(conv.conversion_value), 0) as conversion_value
        FROM `tabClick Event` ce
        JOIN `tabTracked Link` tl ON ce.tracked_link = tl.name
        LEFT JOIN `tabLink Conversion` conv ON conv.tracked_link = tl.name
            AND conv.click_event = ce.name
        WHERE tl.campaign = %(campaign_id)s
            AND ce.timestamp BETWEEN %(start_date)s AND %(end_date)s
        GROUP BY ce.channel
        ORDER BY clicks DESC
    """, {
        'campaign_id': campaign_id,
        'start_date': start_date,
        'end_date': end_date
    }, as_dict=True)
    
    return channels


def get_campaign_timeline(campaign_id, start_date, end_date):
    """Get timeline data for a campaign"""
    
    timeline = frappe.db.sql("""
        SELECT 
            DATE(ce.timestamp) as date,
            COUNT(ce.name) as clicks,
            COUNT(DISTINCT ce.visitor_id) as unique_visitors,
            COUNT(conv.name) as conversions,
            COALESCE(SUM(conv.conversion_value), 0) as conversion_value
        FROM `tabClick Event` ce
        JOIN `tabTracked Link` tl ON ce.tracked_link = tl.name
        LEFT JOIN `tabLink Conversion` conv ON conv.tracked_link = tl.name
            AND conv.click_event = ce.name
            AND DATE(conv.conversion_date) = DATE(ce.timestamp)
        WHERE tl.campaign = %(campaign_id)s
            AND ce.timestamp BETWEEN %(start_date)s AND %(end_date)s
        GROUP BY date
        ORDER BY date
    """, {
        'campaign_id': campaign_id,
        'start_date': start_date,
        'end_date': end_date
    }, as_dict=True)
    
    return timeline
