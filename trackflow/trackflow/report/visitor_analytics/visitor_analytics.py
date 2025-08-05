import frappe
from frappe import _
import json
from datetime import datetime, timedelta

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart_data(filters)
    summary = get_summary(filters)
    
    return columns, data, None, chart, summary

def get_columns():
    return [
        {
            "fieldname": "date",
            "label": _("Date"),
            "fieldtype": "Date",
            "width": 100
        },
        {
            "fieldname": "unique_visitors",
            "label": _("Unique Visitors"),
            "fieldtype": "Int",
            "width": 120
        },
        {
            "fieldname": "total_visits",
            "label": _("Total Visits"),
            "fieldtype": "Int",
            "width": 100
        },
        {
            "fieldname": "page_views",
            "label": _("Page Views"),
            "fieldtype": "Int",
            "width": 100
        },
        {
            "fieldname": "avg_session_duration",
            "label": _("Avg Session Duration"),
            "fieldtype": "Data",
            "width": 150
        },
        {
            "fieldname": "bounce_rate",
            "label": _("Bounce Rate"),
            "fieldtype": "Percent",
            "width": 100
        },
        {
            "fieldname": "new_visitors",
            "label": _("New Visitors"),
            "fieldtype": "Int",
            "width": 100
        },
        {
            "fieldname": "returning_visitors",
            "label": _("Returning Visitors"),
            "fieldtype": "Int",
            "width": 120
        }
    ]

def get_data(filters):
    conditions = get_conditions(filters)
    
    data = frappe.db.sql("""
        SELECT 
            DATE(v.visit_date) as date,
            COUNT(DISTINCT v.visitor_id) as unique_visitors,
            COUNT(*) as total_visits,
            SUM(v.page_views) as page_views,
            AVG(v.session_duration) as avg_session_duration,
            (SUM(CASE WHEN v.page_views = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as bounce_rate,
            COUNT(DISTINCT CASE WHEN v.is_new_visitor = 1 THEN v.visitor_id END) as new_visitors,
            COUNT(DISTINCT CASE WHEN v.is_new_visitor = 0 THEN v.visitor_id END) as returning_visitors
        FROM `tabVisitor Session` v
        WHERE v.docstatus < 2 {conditions}
        GROUP BY DATE(v.visit_date)
        ORDER BY date DESC
    """.format(conditions=conditions), filters, as_dict=1)
    
    # Format session duration
    for row in data:
        if row.avg_session_duration:
            row.avg_session_duration = format_duration(row.avg_session_duration)
    
    return data

def get_conditions(filters):
    conditions = []
    
    if filters.get("from_date"):
        conditions.append("v.visit_date >= %(from_date)s")
    
    if filters.get("to_date"):
        conditions.append("v.visit_date <= %(to_date)s")
    
    if filters.get("campaign"):
        conditions.append("v.campaign = %(campaign)s")
    
    if filters.get("source"):
        conditions.append("v.utm_source = %(source)s")
    
    if filters.get("medium"):
        conditions.append("v.utm_medium = %(medium)s")
    
    return " AND " + " AND ".join(conditions) if conditions else ""

def format_duration(seconds):
    if not seconds:
        return "0s"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"

def get_chart_data(filters):
    conditions = get_conditions(filters)
    
    # Get daily visitor data
    visitor_data = frappe.db.sql("""
        SELECT 
            DATE(visit_date) as date,
            COUNT(DISTINCT visitor_id) as unique_visitors,
            COUNT(*) as total_visits
        FROM `tabVisitor Session`
        WHERE docstatus < 2 {conditions}
        GROUP BY DATE(visit_date)
        ORDER BY date
        LIMIT 30
    """.format(conditions=conditions), filters, as_dict=1)
    
    # Get device type distribution
    device_data = frappe.db.sql("""
        SELECT 
            device_type,
            COUNT(*) as count
        FROM `tabVisitor Session`
        WHERE docstatus < 2 AND device_type IS NOT NULL {conditions}
        GROUP BY device_type
    """.format(conditions=conditions), filters, as_dict=1)
    
    # Get browser distribution
    browser_data = frappe.db.sql("""
        SELECT 
            browser,
            COUNT(*) as count
        FROM `tabVisitor Session`
        WHERE docstatus < 2 AND browser IS NOT NULL {conditions}
        GROUP BY browser
        ORDER BY count DESC
        LIMIT 5
    """.format(conditions=conditions), filters, as_dict=1)
    
    return {
        "data": {
            "labels": [d.date.strftime("%Y-%m-%d") for d in visitor_data],
            "datasets": [
                {
                    "name": "Unique Visitors",
                    "values": [d.unique_visitors for d in visitor_data]
                },
                {
                    "name": "Total Visits",
                    "values": [d.total_visits for d in visitor_data]
                }
            ]
        },
        "type": "line",
        "colors": ["#FF6384", "#36A2EB"],
        "lineOptions": {
            "regionFill": 1
        }
    }

def get_summary(filters):
    conditions = get_conditions(filters)
    
    # Get summary statistics
    summary_data = frappe.db.sql("""
        SELECT 
            COUNT(DISTINCT visitor_id) as total_unique_visitors,
            COUNT(*) as total_visits,
            SUM(page_views) as total_page_views,
            AVG(session_duration) as avg_session_duration,
            AVG(page_views) as avg_pages_per_session,
            (SUM(CASE WHEN page_views = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as overall_bounce_rate
        FROM `tabVisitor Session`
        WHERE docstatus < 2 {conditions}
    """.format(conditions=conditions), filters, as_dict=1)[0]
    
    # Get top pages
    top_pages = frappe.db.sql("""
        SELECT 
            page_url,
            COUNT(*) as views
        FROM `tabPage View`
        WHERE docstatus < 2 {conditions}
        GROUP BY page_url
        ORDER BY views DESC
        LIMIT 5
    """.format(conditions=conditions.replace("v.", "")), filters, as_dict=1)
    
    # Get top referrers
    top_referrers = frappe.db.sql("""
        SELECT 
            referrer,
            COUNT(*) as count
        FROM `tabVisitor Session`
        WHERE docstatus < 2 AND referrer IS NOT NULL AND referrer != '' {conditions}
        GROUP BY referrer
        ORDER BY count DESC
        LIMIT 5
    """.format(conditions=conditions), filters, as_dict=1)
    
    summary = [
        {
            "value": summary_data.total_unique_visitors,
            "label": _("Total Unique Visitors"),
            "datatype": "Int",
            "color": "blue"
        },
        {
            "value": summary_data.total_visits,
            "label": _("Total Visits"),
            "datatype": "Int",
            "color": "green"
        },
        {
            "value": summary_data.total_page_views,
            "label": _("Total Page Views"),
            "datatype": "Int",
            "color": "orange"
        },
        {
            "value": format_duration(summary_data.avg_session_duration) if summary_data.avg_session_duration else "0s",
            "label": _("Avg Session Duration"),
            "datatype": "Data",
            "color": "purple"
        },
        {
            "value": round(summary_data.avg_pages_per_session, 2) if summary_data.avg_pages_per_session else 0,
            "label": _("Avg Pages Per Session"),
            "datatype": "Float",
            "color": "yellow"
        },
        {
            "value": round(summary_data.overall_bounce_rate, 2) if summary_data.overall_bounce_rate else 0,
            "label": _("Overall Bounce Rate %"),
            "datatype": "Percent",
            "color": "red"
        }
    ]
    
    return summary
