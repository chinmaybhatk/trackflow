import frappe
from frappe import _
import json
from datetime import datetime, timedelta

@frappe.whitelist()
def get_dashboard_data():
    """Get comprehensive dashboard data for TrackFlow analytics."""
    if not frappe.has_permission("Campaign", "read"):
        frappe.throw(_("You don't have permission to access this data"))
    
    # Get date range (last 30 days by default)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    data = {
        "summary": get_summary_stats(start_date, end_date),
        "campaigns": get_campaign_performance(start_date, end_date),
        "sources": get_source_performance(start_date, end_date),
        "conversions": get_conversion_data(start_date, end_date),
        "devices": get_device_data(start_date, end_date),
        "locations": get_location_data(start_date, end_date),
        "recent_visitors": get_recent_visitors(),
        "attribution": get_attribution_data(start_date, end_date)
    }
    
    return data

def get_summary_stats(start_date, end_date):
    """Get summary statistics."""
    total_visitors = frappe.db.count("Visitor", {
        "first_seen": ["between", [start_date, end_date]]
    })
    
    total_sessions = frappe.db.count("Visitor Session", {
        "start_time": ["between", [start_date, end_date]]
    })
    
    total_page_views = frappe.db.count("Page View", {
        "timestamp": ["between", [start_date, end_date]]
    })
    
    total_conversions = frappe.db.count("Conversion", {
        "timestamp": ["between", [start_date, end_date]]
    })
    
    # Calculate conversion rate
    conversion_rate = (total_conversions / total_visitors * 100) if total_visitors > 0 else 0
    
    # Calculate average session duration
    avg_duration = frappe.db.sql("""
        SELECT AVG(duration) as avg_duration
        FROM `tabVisitor Session`
        WHERE start_time BETWEEN %s AND %s
    """, (start_date, end_date), as_dict=True)
    
    avg_session_duration = avg_duration[0].avg_duration if avg_duration else 0
    
    return {
        "total_visitors": total_visitors,
        "total_sessions": total_sessions,
        "total_page_views": total_page_views,
        "total_conversions": total_conversions,
        "conversion_rate": round(conversion_rate, 2),
        "avg_session_duration": round(avg_session_duration or 0, 2)
    }

def get_campaign_performance(start_date, end_date):
    """Get campaign performance data."""
    campaigns = frappe.db.sql("""
        SELECT 
            c.name,
            c.campaign_name,
            c.source,
            c.medium,
            COUNT(DISTINCT v.name) as visitors,
            COUNT(DISTINCT vs.name) as sessions,
            COUNT(DISTINCT pv.name) as page_views,
            COUNT(DISTINCT conv.name) as conversions,
            SUM(conv.value) as total_value
        FROM `tabCampaign` c
        LEFT JOIN `tabVisitor` v ON v.utm_campaign = c.campaign_name
        LEFT JOIN `tabVisitor Session` vs ON vs.visitor = v.name 
            AND vs.start_time BETWEEN %(start_date)s AND %(end_date)s
        LEFT JOIN `tabPage View` pv ON pv.session = vs.name
        LEFT JOIN `tabConversion` conv ON conv.visitor = v.name
            AND conv.timestamp BETWEEN %(start_date)s AND %(end_date)s
        WHERE c.status = 'Active'
        GROUP BY c.name
        ORDER BY visitors DESC
        LIMIT 10
    """, {
        "start_date": start_date,
        "end_date": end_date
    }, as_dict=True)
    
    # Calculate conversion rates and ROI
    for campaign in campaigns:
        campaign["conversion_rate"] = round(
            (campaign["conversions"] / campaign["visitors"] * 100) 
            if campaign["visitors"] > 0 else 0, 2
        )
        campaign["total_value"] = campaign["total_value"] or 0
    
    return campaigns

def get_source_performance(start_date, end_date):
    """Get traffic source performance."""
    sources = frappe.db.sql("""
        SELECT 
            COALESCE(v.utm_source, 'Direct') as source,
            COUNT(DISTINCT v.name) as visitors,
            COUNT(DISTINCT vs.name) as sessions,
            COUNT(DISTINCT conv.name) as conversions,
            SUM(conv.value) as total_value
        FROM `tabVisitor` v
        LEFT JOIN `tabVisitor Session` vs ON vs.visitor = v.name
            AND vs.start_time BETWEEN %(start_date)s AND %(end_date)s
        LEFT JOIN `tabConversion` conv ON conv.visitor = v.name
            AND conv.timestamp BETWEEN %(start_date)s AND %(end_date)s
        WHERE v.first_seen BETWEEN %(start_date)s AND %(end_date)s
        GROUP BY source
        ORDER BY visitors DESC
    """, {
        "start_date": start_date,
        "end_date": end_date
    }, as_dict=True)
    
    return sources

def get_conversion_data(start_date, end_date):
    """Get conversion funnel data."""
    conversions = frappe.db.sql("""
        SELECT 
            DATE(timestamp) as date,
            conversion_type,
            COUNT(*) as count,
            SUM(value) as total_value
        FROM `tabConversion`
        WHERE timestamp BETWEEN %s AND %s
        GROUP BY date, conversion_type
        ORDER BY date
    """, (start_date, end_date), as_dict=True)
    
    # Group by date for chart
    date_data = {}
    for conv in conversions:
        date_str = conv["date"].strftime("%Y-%m-%d")
        if date_str not in date_data:
            date_data[date_str] = {
                "date": date_str,
                "total": 0,
                "value": 0,
                "types": {}
            }
        date_data[date_str]["total"] += conv["count"]
        date_data[date_str]["value"] += conv["total_value"] or 0
        date_data[date_str]["types"][conv["conversion_type"]] = conv["count"]
    
    return list(date_data.values())

def get_device_data(start_date, end_date):
    """Get device and browser data."""
    devices = frappe.db.sql("""
        SELECT 
            device_type,
            browser,
            COUNT(DISTINCT visitor) as visitors,
            COUNT(*) as sessions
        FROM `tabVisitor Session`
        WHERE start_time BETWEEN %s AND %s
        GROUP BY device_type, browser
        ORDER BY sessions DESC
    """, (start_date, end_date), as_dict=True)
    
    # Aggregate by device type
    device_summary = {}
    for device in devices:
        device_type = device["device_type"] or "Unknown"
        if device_type not in device_summary:
            device_summary[device_type] = {
                "visitors": 0,
                "sessions": 0,
                "browsers": {}
            }
        device_summary[device_type]["visitors"] += device["visitors"]
        device_summary[device_type]["sessions"] += device["sessions"]
        
        browser = device["browser"] or "Unknown"
        if browser not in device_summary[device_type]["browsers"]:
            device_summary[device_type]["browsers"][browser] = 0
        device_summary[device_type]["browsers"][browser] += device["sessions"]
    
    return device_summary

def get_location_data(start_date, end_date):
    """Get geographic location data."""
    locations = frappe.db.sql("""
        SELECT 
            country,
            city,
            COUNT(DISTINCT visitor) as visitors,
            COUNT(*) as sessions
        FROM `tabVisitor Session`
        WHERE start_time BETWEEN %s AND %s
            AND country IS NOT NULL
        GROUP BY country, city
        ORDER BY visitors DESC
        LIMIT 20
    """, (start_date, end_date), as_dict=True)
    
    return locations

def get_recent_visitors():
    """Get recent visitor activity."""
    recent = frappe.db.sql("""
        SELECT 
            v.name,
            v.visitor_id,
            v.first_seen,
            v.last_seen,
            v.utm_source,
            v.utm_campaign,
            vs.device_type,
            vs.browser,
            vs.country,
            vs.city,
            COUNT(DISTINCT vs.name) as session_count,
            COUNT(DISTINCT pv.name) as page_view_count
        FROM `tabVisitor` v
        LEFT JOIN `tabVisitor Session` vs ON vs.visitor = v.name
        LEFT JOIN `tabPage View` pv ON pv.session = vs.name
        WHERE v.last_seen >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        GROUP BY v.name
        ORDER BY v.last_seen DESC
        LIMIT 50
    """, as_dict=True)
    
    return recent

def get_attribution_data(start_date, end_date):
    """Get attribution model data."""
    attribution = frappe.db.sql("""
        SELECT 
            am.model_name,
            am.model_type,
            da.touchpoint_type,
            da.touchpoint_source,
            SUM(da.attributed_value) as total_attributed_value,
            COUNT(DISTINCT da.deal) as deals_influenced
        FROM `tabDeal Attribution` da
        INNER JOIN `tabAttribution Model` am ON am.name = da.attribution_model
        WHERE da.created >= %s AND da.created <= %s
        GROUP BY am.name, da.touchpoint_type, da.touchpoint_source
        ORDER BY total_attributed_value DESC
    """, (start_date, end_date), as_dict=True)
    
    return attribution

@frappe.whitelist()
def get_chart_data(chart_type, start_date=None, end_date=None):
    """Get specific chart data based on type."""
    if not frappe.has_permission("Campaign", "read"):
        frappe.throw(_("You don't have permission to access this data"))
    
    if not start_date:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
    else:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
    
    if chart_type == "visitor_trend":
        return get_visitor_trend(start_date, end_date)
    elif chart_type == "conversion_funnel":
        return get_conversion_funnel(start_date, end_date)
    elif chart_type == "source_breakdown":
        return get_source_breakdown(start_date, end_date)
    else:
        frappe.throw(_("Invalid chart type"))

def get_visitor_trend(start_date, end_date):
    """Get visitor trend data for line chart."""
    data = frappe.db.sql("""
        SELECT 
            DATE(first_seen) as date,
            COUNT(*) as new_visitors,
            (SELECT COUNT(*) FROM `tabVisitor` v2 
             WHERE DATE(v2.last_seen) = DATE(v1.first_seen) 
               AND v2.first_seen < DATE(v1.first_seen)) as returning_visitors
        FROM `tabVisitor` v1
        WHERE first_seen BETWEEN %s AND %s
        GROUP BY date
        ORDER BY date
    """, (start_date, end_date), as_dict=True)
    
    return data

def get_conversion_funnel(start_date, end_date):
    """Get conversion funnel data."""
    total_visitors = frappe.db.count("Visitor", {
        "first_seen": ["between", [start_date, end_date]]
    })
    
    total_sessions = frappe.db.count("Visitor Session", {
        "start_time": ["between", [start_date, end_date]]
    })
    
    total_engaged = frappe.db.sql("""
        SELECT COUNT(DISTINCT visitor) as count
        FROM `tabVisitor Session`
        WHERE start_time BETWEEN %s AND %s
            AND duration > 30
    """, (start_date, end_date), as_dict=True)[0]["count"]
    
    total_conversions = frappe.db.count("Conversion", {
        "timestamp": ["between", [start_date, end_date]]
    })
    
    return [
        {"stage": "Visitors", "count": total_visitors},
        {"stage": "Sessions", "count": total_sessions},
        {"stage": "Engaged", "count": total_engaged},
        {"stage": "Converted", "count": total_conversions}
    ]

def get_source_breakdown(start_date, end_date):
    """Get traffic source breakdown for pie chart."""
    sources = frappe.db.sql("""
        SELECT 
            COALESCE(utm_source, 'Direct') as source,
            COUNT(*) as count
        FROM `tabVisitor`
        WHERE first_seen BETWEEN %s AND %s
        GROUP BY source
        ORDER BY count DESC
        LIMIT 10
    """, (start_date, end_date), as_dict=True)
    
    return sources