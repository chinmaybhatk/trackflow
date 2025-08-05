"""
TrackFlow Scheduled Tasks
"""

import frappe
from frappe.utils import now_datetime, add_days
from datetime import datetime, timedelta

def process_click_queue():
    """
    Process queued click events for better performance
    """
    # Get pending click events from queue
    pending_clicks = frappe.get_all(
        "Click Queue",
        filters={"status": "Pending"},
        limit=100,
        order_by="creation asc"
    )
    
    for click in pending_clicks:
        try:
            process_single_click(click.name)
            frappe.db.commit()
        except Exception as e:
            frappe.log_error(f"Error processing click {click.name}: {str(e)}")
            frappe.db.rollback()

def cleanup_expired_links():
    """
    Mark expired links as inactive
    """
    expired_links = frappe.get_all(
        "Tracked Link",
        filters={
            "expiry_date": ["<", now_datetime()],
            "status": "Active"
        },
        pluck="name"
    )
    
    for link_name in expired_links:
        link = frappe.get_doc("Tracked Link", link_name)
        link.status = "Expired"
        link.save(ignore_permissions=True)
    
    frappe.db.commit()
    
    return f"Marked {len(expired_links)} links as expired"

def generate_daily_reports():
    """
    Generate daily analytics reports
    """
    yesterday = add_days(now_datetime(), -1)
    
    # Get all active campaigns
    campaigns = frappe.get_all(
        "Link Campaign",
        filters={"status": "Active"},
        pluck="name"
    )
    
    for campaign in campaigns:
        generate_campaign_report(campaign, yesterday)
    
    # Send summary email to admins
    send_daily_summary(yesterday)

def send_weekly_analytics():
    """
    Send weekly analytics digest to users
    """
    # Get users who opted in for weekly reports
    users = frappe.get_all(
        "User",
        filters={"trackflow_weekly_digest": 1},
        pluck="name"
    )
    
    for user in users:
        send_user_analytics_digest(user)

def process_single_click(queue_name):
    """
    Process a single click from queue
    """
    queue_doc = frappe.get_doc("Click Queue", queue_name)
    
    # Create click event
    click_event = frappe.get_doc({
        "doctype": "Click Event",
        "tracked_link": queue_doc.tracked_link,
        "timestamp": queue_doc.timestamp,
        "ip_address": queue_doc.ip_address,
        "user_agent": queue_doc.user_agent,
        "referrer": queue_doc.referrer,
        "country": queue_doc.country,
        "city": queue_doc.city
    })
    
    click_event.insert(ignore_permissions=True)
    
    # Update link statistics
    update_link_stats(queue_doc.tracked_link)
    
    # Mark queue item as processed
    queue_doc.status = "Processed"
    queue_doc.save(ignore_permissions=True)

def update_link_stats(link_name):
    """
    Update link click statistics
    """
    link = frappe.get_doc("Tracked Link", link_name)
    
    # Update click count
    link.total_clicks = frappe.db.count("Click Event", {"tracked_link": link_name})
    
    # Update unique visitors
    unique_ips = frappe.db.sql("""
        SELECT COUNT(DISTINCT ip_address) 
        FROM `tabClick Event` 
        WHERE tracked_link = %s
    """, link_name)[0][0]
    
    link.unique_visitors = unique_ips
    link.save(ignore_permissions=True)

def generate_campaign_report(campaign_name, date):
    """
    Generate report for a specific campaign
    """
    # Implementation for campaign report generation
    pass

def send_daily_summary(date):
    """
    Send daily summary email
    """
    # Implementation for daily summary
    pass

def send_user_analytics_digest(user):
    """
    Send weekly digest to user
    """
    # Implementation for user digest
    pass