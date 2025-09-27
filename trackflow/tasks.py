"""
Scheduled tasks for TrackFlow
"""

import frappe
from frappe import _
from datetime import datetime, timedelta

def process_visitor_sessions():
    """Process visitor sessions and update metrics"""
    # Get active sessions that haven't been updated in 30 minutes
    stale_time = frappe.utils.add_to_date(frappe.utils.now(), minutes=-30)
    
    sessions = frappe.get_all(
        "Visitor Session",
        filters={
            "end_time": None,
            "last_activity": ["<", stale_time]
        },
        fields=["name", "visitor", "start_time", "last_activity"]
    )
    
    for session in sessions:
        # Mark session as ended
        doc = frappe.get_doc("Visitor Session", session.name)
        doc.end_time = session.last_activity
        doc.duration = calculate_duration(session.start_time, session.last_activity)
        doc.save(ignore_permissions=True)

def update_campaign_metrics():
    """Update campaign metrics from tracking data"""
    campaigns = frappe.get_all(
        "Link Campaign",
        filters={"status": "Active"},
        fields=["name"]
    )
    
    for campaign in campaigns:
        update_single_campaign_metrics(campaign.name)

def update_single_campaign_metrics(campaign_name):
    """Update metrics for a single campaign"""
    # Get all tracking links for this campaign
    links = frappe.get_all(
        "Tracked Link",
        filters={"campaign": campaign_name},
        fields=["name", "total_clicks"]
    )
    
    total_clicks = sum(link.total_clicks or 0 for link in links)
    
    # Get conversions
    conversions = frappe.db.count(
        "CRM Lead",
        filters={"trackflow_campaign": campaign_name}
    )
    
    # Update campaign
    campaign = frappe.get_doc("Link Campaign", campaign_name)
    campaign.total_clicks = total_clicks
    campaign.conversions = conversions
    
    if total_clicks > 0:
        campaign.conversion_rate = (conversions / total_clicks) * 100
    else:
        campaign.conversion_rate = 0
        
    campaign.save(ignore_permissions=True)

def cleanup_expired_data():
    """Clean up expired tracking data"""
    settings = frappe.get_single("TrackFlow Settings")
    
    # Calculate cutoff date
    cutoff_date = frappe.utils.add_to_date(
        frappe.utils.today(),
        days=-(settings.data_retention_days or 90)
    )
    
    # Delete old visitor events
    frappe.db.delete(
        "Visitor Event",
        {"timestamp": ["<", cutoff_date]}
    )
    
    # Delete old sessions
    frappe.db.delete(
        "Visitor Session",
        {"start_time": ["<", cutoff_date]}
    )

def generate_daily_reports():
    """Generate daily analytics reports"""
    # Get yesterday's date range
    yesterday = frappe.utils.add_to_date(frappe.utils.today(), days=-1)
    start_date = frappe.utils.get_datetime_str(yesterday + " 00:00:00")
    end_date = frappe.utils.get_datetime_str(yesterday + " 23:59:59")
    
    # Generate report data
    report_data = {
        "date": yesterday,
        "visitors": get_visitor_count(start_date, end_date),
        "page_views": get_page_view_count(start_date, end_date),
        "conversions": get_conversion_count(start_date, end_date),
        "top_pages": get_top_pages(start_date, end_date),
        "top_sources": get_top_sources(start_date, end_date)
    }
    
    # Store report
    report = frappe.new_doc("TrackFlow Daily Report")
    report.report_date = yesterday
    report.report_data = frappe.as_json(report_data)
    report.insert(ignore_permissions=True)

def calculate_attribution():
    """Calculate attribution for recent conversions"""
    # Get deals that need attribution calculation
    deals = frappe.get_all(
        "CRM Deal",
        filters={
            "stage": "Won",
            "trackflow_attribution_data": None,
            "trackflow_marketing_influenced": 1
        },
        fields=["name"]
    )
    
    for deal in deals:
        try:
            from trackflow.integrations.crm_deal import calculate_attribution as calc_deal_attr
            deal_doc = frappe.get_doc("CRM Deal", deal.name)
            calc_deal_attr(deal_doc, None)
        except Exception as e:
            frappe.log_error(f"Attribution calculation error for {deal.name}: {str(e)}")

def update_visitor_profiles():
    """Update visitor profiles with aggregated data"""
    # Get visitors that need profile updates
    visitors = frappe.get_all(
        "Visitor",
        filters={
            "profile_updated": None
        },
        fields=["name"],
        limit=100
    )
    
    for visitor in visitors:
        update_single_visitor_profile(visitor.name)

def update_single_visitor_profile(visitor_name):
    """Update profile for a single visitor"""
    visitor = frappe.get_doc("Visitor", visitor_name)
    
    # Calculate engagement score
    engagement_score = 0
    
    # Page views
    page_views = frappe.db.count(
        "Visitor Event",
        filters={
            "visitor": visitor_name,
            "event_type": "page_view"
        }
    )
    engagement_score += page_views * 1
    
    # Form submissions
    form_submissions = frappe.db.count(
        "Visitor Event",
        filters={
            "visitor": visitor_name,
            "event_type": "form_submission"
        }
    )
    engagement_score += form_submissions * 10
    
    # Update visitor
    visitor.engagement_score = engagement_score
    visitor.profile_updated = frappe.utils.now()
    visitor.save(ignore_permissions=True)

def send_weekly_analytics():
    """Send weekly analytics email"""
    from trackflow.notifications import send_weekly_report
    send_weekly_report()

def cleanup_old_visitors():
    """Clean up old visitor data"""
    # Remove visitors with no activity in 180 days
    cutoff_date = frappe.utils.add_to_date(frappe.utils.today(), days=-180)
    
    old_visitors = frappe.get_all(
        "Visitor",
        filters={
            "last_seen": ["<", cutoff_date],
            "lead": None,
            "organization": None
        },
        fields=["name"]
    )
    
    for visitor in old_visitors:
        frappe.delete_doc("Visitor", visitor.name, ignore_permissions=True)

def generate_attribution_reports():
    """Generate weekly attribution reports"""
    # This is a placeholder for attribution report generation
    pass

# Helper functions
def calculate_duration(start_time, end_time):
    """Calculate duration in seconds"""
    if not start_time or not end_time:
        return 0
    start = frappe.utils.get_datetime(start_time)
    end = frappe.utils.get_datetime(end_time)
    return int((end - start).total_seconds())

def get_visitor_count(start_date, end_date):
    """Get unique visitor count for date range"""
    return frappe.db.sql("""
        SELECT COUNT(DISTINCT visitor) 
        FROM `tabVisitor Event`
        WHERE timestamp BETWEEN %s AND %s
    """, (start_date, end_date))[0][0]

def get_page_view_count(start_date, end_date):
    """Get page view count for date range"""
    return frappe.db.count(
        "Visitor Event",
        filters={
            "event_type": "page_view",
            "timestamp": ["between", [start_date, end_date]]
        }
    )

def get_conversion_count(start_date, end_date):
    """Get conversion count for date range"""
    return frappe.db.count(
        "CRM Lead",
        filters={
            "creation": ["between", [start_date, end_date]],
            "trackflow_visitor_id": ["!=", None]
        }
    )

def get_top_pages(start_date, end_date, limit=10):
    """Get top pages by views"""
    return frappe.db.sql("""
        SELECT url, COUNT(*) as views
        FROM `tabVisitor Event`
        WHERE event_type = 'page_view'
        AND timestamp BETWEEN %s AND %s
        GROUP BY url
        ORDER BY views DESC
        LIMIT %s
    """, (start_date, end_date, limit), as_dict=True)

def get_top_sources(start_date, end_date, limit=10):
    """Get top traffic sources"""
    return frappe.db.sql("""
        SELECT source, COUNT(DISTINCT visitor) as visitors
        FROM `tabVisitor`
        WHERE first_seen BETWEEN %s AND %s
        GROUP BY source
        ORDER BY visitors DESC
        LIMIT %s
    """, (start_date, end_date, limit), as_dict=True)
