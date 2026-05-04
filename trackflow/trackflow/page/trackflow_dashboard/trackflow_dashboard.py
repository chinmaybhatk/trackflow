"""TrackFlow Dashboard backend.

Provides aggregate metrics from the live schema: Click Event, Visitor,
Conversion, Link Campaign, Tracked Link. Returns shapes the existing
trackflow_dashboard.js consumes; missing data points are returned as
empty lists / zeros instead of raising.
"""

import frappe
from frappe import _
from datetime import datetime, timedelta


@frappe.whitelist()
def get_dashboard_data():
    """Return all dashboard panels for the last 30 days."""
    if not frappe.has_permission("Link Campaign", "read"):
        frappe.throw(_("You don't have permission to access this data"))

    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    return {
        "summary": get_summary_stats(start_date, end_date),
        "campaigns": get_campaign_performance(start_date, end_date),
        "sources": get_source_performance(start_date, end_date),
        "conversions": get_conversion_data(start_date, end_date),
        "devices": {},
        "locations": [],
        "recent_visitors": get_recent_visitors(),
        "attribution": [],
    }


def get_summary_stats(start_date, end_date):
    """Top-row KPI cards.

    Conversion rate is computed as:
        distinct visitors who converted in the window
        / distinct visitors active in the window (had >= 1 click)
        * 100

    This bounds the rate to 0–100% and counts each visitor once,
    regardless of how many click/conversion rows they have.
    """
    total_visitors = frappe.db.count("Visitor", {"first_seen": ["between", [start_date, end_date]]})

    total_clicks = frappe.db.sql(
        "SELECT COUNT(*) FROM `tabClick Event` WHERE click_timestamp BETWEEN %s AND %s",
        (start_date, end_date),
    )[0][0] or 0

    total_conversions = frappe.db.sql(
        "SELECT COUNT(*) FROM `tabConversion` WHERE conversion_timestamp BETWEEN %s AND %s",
        (start_date, end_date),
    )[0][0] or 0

    active_visitors = frappe.db.sql(
        """
        SELECT COUNT(DISTINCT visitor_id) FROM `tabClick Event`
        WHERE click_timestamp BETWEEN %s AND %s AND visitor_id IS NOT NULL
        """,
        (start_date, end_date),
    )[0][0] or 0

    converted_visitors = frappe.db.sql(
        """
        SELECT COUNT(DISTINCT visitor_id) FROM `tabConversion`
        WHERE conversion_timestamp BETWEEN %s AND %s AND visitor_id IS NOT NULL
        """,
        (start_date, end_date),
    )[0][0] or 0

    conversion_rate = (converted_visitors / active_visitors * 100) if active_visitors else 0

    return {
        "total_visitors": total_visitors,
        "total_sessions": total_clicks,
        "total_page_views": total_clicks,
        "total_conversions": total_conversions,
        "conversion_rate": round(conversion_rate, 2),
        "avg_session_duration": 0,
    }


def get_campaign_performance(start_date, end_date):
    """Top campaigns by clicks."""
    campaigns = frappe.db.sql(
        """
        SELECT
            c.name,
            c.campaign_name,
            c.source,
            c.medium,
            COUNT(DISTINCT ce.visitor_id) as visitors,
            COUNT(ce.name)               as sessions,
            COUNT(ce.name)               as page_views,
            COUNT(DISTINCT lc.name)      as conversions,
            COALESCE(SUM(lc.conversion_value), 0) as total_value
        FROM `tabLink Campaign` c
        LEFT JOIN `tabClick Event` ce
            ON ce.campaign = c.name
            AND ce.click_timestamp BETWEEN %(start_date)s AND %(end_date)s
        LEFT JOIN `tabConversion` lc
            ON lc.campaign = c.name
            AND lc.conversion_timestamp BETWEEN %(start_date)s AND %(end_date)s
        WHERE c.status = 'Active'
        GROUP BY c.name
        ORDER BY visitors DESC
        LIMIT 10
        """,
        {"start_date": start_date, "end_date": end_date},
        as_dict=True,
    )

    for c in campaigns:
        c["conversion_rate"] = round(
            (c["conversions"] / c["visitors"] * 100) if c["visitors"] else 0, 2
        )
        c["total_value"] = c["total_value"] or 0

    return campaigns


def get_source_performance(start_date, end_date):
    """Traffic source breakdown from Click Event."""
    return frappe.db.sql(
        """
        SELECT
            COALESCE(utm_source, 'Direct') as source,
            COUNT(DISTINCT visitor_id)     as visitors,
            COUNT(name)                    as sessions,
            0                              as conversions,
            0                              as total_value
        FROM `tabClick Event`
        WHERE click_timestamp BETWEEN %s AND %s
        GROUP BY source
        ORDER BY visitors DESC
        """,
        (start_date, end_date),
        as_dict=True,
    )


def get_conversion_data(start_date, end_date):
    """Daily conversion timeseries."""
    rows = frappe.db.sql(
        """
        SELECT
            DATE(conversion_timestamp) as date,
            conversion_type,
            COUNT(*) as count,
            COALESCE(SUM(conversion_value), 0) as total_value
        FROM `tabConversion`
        WHERE conversion_timestamp BETWEEN %s AND %s
        GROUP BY date, conversion_type
        ORDER BY date
        """,
        (start_date, end_date),
        as_dict=True,
    )

    by_date = {}
    for r in rows:
        date_str = r["date"].strftime("%Y-%m-%d") if r["date"] else ""
        bucket = by_date.setdefault(
            date_str, {"date": date_str, "total": 0, "value": 0, "types": {}}
        )
        bucket["total"] += r["count"]
        bucket["value"] += r["total_value"] or 0
        bucket["types"][r["conversion_type"] or "unknown"] = r["count"]
    return list(by_date.values())


def get_recent_visitors():
    """Recent active visitors."""
    return frappe.db.sql(
        """
        SELECT
            v.name,
            v.visitor_id,
            v.first_seen,
            v.last_seen,
            v.source       as utm_source,
            v.campaign     as utm_campaign,
            NULL           as device_type,
            NULL           as browser,
            NULL           as country,
            NULL           as city,
            v.page_views   as session_count,
            v.page_views   as page_view_count
        FROM `tabVisitor` v
        WHERE v.last_seen >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        ORDER BY v.last_seen DESC
        LIMIT 50
        """,
        as_dict=True,
    )


@frappe.whitelist()
def get_chart_data(chart_type, start_date=None, end_date=None):
    """Chart data endpoint used by drill-down panels."""
    if not frappe.has_permission("Link Campaign", "read"):
        frappe.throw(_("You don't have permission to access this data"))

    if not start_date:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
    else:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")

    if chart_type == "visitor_trend":
        return get_visitor_trend(start_date, end_date)
    if chart_type == "conversion_funnel":
        return get_conversion_funnel(start_date, end_date)
    if chart_type == "source_breakdown":
        return get_source_breakdown(start_date, end_date)
    frappe.throw(_("Invalid chart type"))


def get_visitor_trend(start_date, end_date):
    return frappe.db.sql(
        """
        SELECT
            DATE(first_seen) as date,
            COUNT(*) as new_visitors,
            0 as returning_visitors
        FROM `tabVisitor`
        WHERE first_seen BETWEEN %s AND %s
        GROUP BY date
        ORDER BY date
        """,
        (start_date, end_date),
        as_dict=True,
    )


def get_conversion_funnel(start_date, end_date):
    total_visitors = frappe.db.count("Visitor", {"first_seen": ["between", [start_date, end_date]]})
    total_clicks = frappe.db.sql(
        "SELECT COUNT(*) FROM `tabClick Event` WHERE click_timestamp BETWEEN %s AND %s",
        (start_date, end_date),
    )[0][0] or 0
    total_conversions = frappe.db.sql(
        "SELECT COUNT(*) FROM `tabConversion` WHERE conversion_timestamp BETWEEN %s AND %s",
        (start_date, end_date),
    )[0][0] or 0

    return [
        {"stage": "Visitors", "count": total_visitors},
        {"stage": "Clicks", "count": total_clicks},
        {"stage": "Converted", "count": total_conversions},
    ]


def get_source_breakdown(start_date, end_date):
    return frappe.db.sql(
        """
        SELECT
            COALESCE(source, 'Direct') as source,
            COUNT(*) as count
        FROM `tabVisitor`
        WHERE first_seen BETWEEN %s AND %s
        GROUP BY source
        ORDER BY count DESC
        LIMIT 10
        """,
        (start_date, end_date),
        as_dict=True,
    )
