import frappe
from frappe import _
from datetime import datetime, timedelta

def get_context(context):
    """FCRM-style analytics dashboard"""
    context.no_cache = 1
    context.show_sidebar = False
    
    # Get dashboard data
    dashboard_data = get_dashboard_data()
    
    context.update({
        "title": _("TrackFlow Analytics"),
        "dashboard_data": dashboard_data,
        "page_name": "analytics",
        "show_crm_navbar": True
    })
    
    return context

def get_dashboard_data():
    """Get comprehensive analytics data"""
    
    # Date ranges
    today = datetime.now().date()
    last_30_days = today - timedelta(days=30)
    last_7_days = today - timedelta(days=7)
    
    # Total stats
    total_campaigns = frappe.db.count("Link Campaign")
    total_links = frappe.db.count("Tracked Link")
    total_clicks = frappe.db.count("Click Event")
    total_conversions = frappe.db.count("Conversion")
    
    # Recent stats (last 30 days)
    recent_clicks = frappe.db.sql("""
        SELECT COUNT(*) as count
        FROM `tabClick Event`
        WHERE DATE(creation) >= %s
    """, last_30_days, as_dict=True)[0].count or 0
    
    recent_conversions = frappe.db.sql("""
        SELECT COUNT(*) as count
        FROM `tabConversion`
        WHERE DATE(conversion_date) >= %s
    """, last_30_days, as_dict=True)[0].count or 0
    
    # Conversion rate
    conversion_rate = (recent_conversions / recent_clicks * 100) if recent_clicks > 0 else 0
    
    # Top campaigns by clicks
    top_campaigns = frappe.db.sql("""
        SELECT 
            lc.campaign_name,
            lc.name,
            COUNT(ce.name) as clicks,
            COUNT(DISTINCT ce.visitor) as unique_visitors
        FROM `tabLink Campaign` lc
        LEFT JOIN `tabClick Event` ce ON ce.campaign = lc.name
        WHERE DATE(ce.creation) >= %s OR ce.creation IS NULL
        GROUP BY lc.name, lc.campaign_name
        ORDER BY clicks DESC
        LIMIT 5
    """, last_30_days, as_dict=True)
    
    # Top links by clicks
    top_links = frappe.db.sql("""
        SELECT 
            tl.link_name,
            tl.name,
            tl.short_code,
            COUNT(ce.name) as clicks
        FROM `tabTracked Link` tl
        LEFT JOIN `tabClick Event` ce ON ce.tracked_link = tl.name
        WHERE DATE(ce.creation) >= %s OR ce.creation IS NULL
        GROUP BY tl.name, tl.link_name, tl.short_code
        ORDER BY clicks DESC
        LIMIT 5
    """, last_30_days, as_dict=True)
    
    # Daily clicks for chart (last 14 days)
    daily_clicks = frappe.db.sql("""
        SELECT 
            DATE(creation) as date,
            COUNT(*) as clicks,
            COUNT(DISTINCT visitor) as unique_visitors
        FROM `tabClick Event`
        WHERE DATE(creation) >= %s
        GROUP BY DATE(creation)
        ORDER BY date ASC
    """, today - timedelta(days=14), as_dict=True)
    
    # Geographic distribution
    geo_data = frappe.db.sql("""
        SELECT 
            country,
            COUNT(*) as clicks
        FROM `tabClick Event`
        WHERE country IS NOT NULL 
        AND DATE(creation) >= %s
        GROUP BY country
        ORDER BY clicks DESC
        LIMIT 10
    """, last_30_days, as_dict=True)
    
    # Device/browser stats
    device_stats = frappe.db.sql("""
        SELECT 
            device_type,
            COUNT(*) as clicks
        FROM `tabClick Event`
        WHERE DATE(creation) >= %s
        GROUP BY device_type
        ORDER BY clicks DESC
    """, last_30_days, as_dict=True)
    
    browser_stats = frappe.db.sql("""
        SELECT 
            browser,
            COUNT(*) as clicks
        FROM `tabClick Event`
        WHERE DATE(creation) >= %s
        AND browser IS NOT NULL
        GROUP BY browser
        ORDER BY clicks DESC
        LIMIT 5
    """, last_30_days, as_dict=True)
    
    # Recent activity
    recent_activity = frappe.db.sql("""
        SELECT 
            'click' as type,
            ce.creation,
            tl.link_name as title,
            ce.browser,
            ce.device_type,
            ce.country
        FROM `tabClick Event` ce
        LEFT JOIN `tabTracked Link` tl ON tl.name = ce.tracked_link
        WHERE DATE(ce.creation) >= %s
        
        UNION ALL
        
        SELECT 
            'conversion' as type,
            c.conversion_date as creation,
            c.conversion_type as title,
            NULL as browser,
            NULL as device_type,
            NULL as country
        FROM `tabConversion` c
        WHERE DATE(c.conversion_date) >= %s
        
        ORDER BY creation DESC
        LIMIT 10
    """, (last_7_days, last_7_days), as_dict=True)
    
    return {
        "total_stats": {
            "campaigns": total_campaigns,
            "links": total_links,
            "clicks": total_clicks,
            "conversions": total_conversions
        },
        "recent_stats": {
            "clicks": recent_clicks,
            "conversions": recent_conversions,
            "conversion_rate": round(conversion_rate, 2)
        },
        "top_campaigns": top_campaigns,
        "top_links": top_links,
        "daily_clicks": daily_clicks,
        "geo_data": geo_data,
        "device_stats": device_stats,
        "browser_stats": browser_stats,
        "recent_activity": recent_activity
    }

@frappe.whitelist()
def get_campaign_analytics(campaign_name, days=30):
    """Get analytics for a specific campaign"""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=int(days))
    
    # Daily clicks for the campaign
    daily_data = frappe.db.sql("""
        SELECT 
            DATE(creation) as date,
            COUNT(*) as clicks,
            COUNT(DISTINCT visitor) as unique_visitors
        FROM `tabClick Event`
        WHERE campaign = %s
        AND DATE(creation) BETWEEN %s AND %s
        GROUP BY DATE(creation)
        ORDER BY date ASC
    """, (campaign_name, start_date, end_date), as_dict=True)
    
    return {"daily_data": daily_data}