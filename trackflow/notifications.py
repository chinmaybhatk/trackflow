"""
Notifications module for TrackFlow
"""

import frappe
from frappe import _

def get_notification_config():
    """Get notification configuration for TrackFlow"""
    return {
        "for_doctype": {
            "Campaign": {
                "status": ("in", ["Active", "Paused"]),
            },
            "Tracked Link": {
                "total_clicks": (">", 100),
            }
        }
    }

def check_campaign_performance():
    """Check campaign performance and send alerts"""
    settings = frappe.get_single("TrackFlow Settings")
    
    if not settings.enable_notifications:
        return
        
    # Check for campaigns exceeding thresholds
    campaigns = frappe.get_all(
        "Campaign",
        filters={"status": "Active"},
        fields=["name", "campaign_name", "total_clicks", "conversion_rate"]
    )
    
    for campaign in campaigns:
        # Check visit threshold
        if campaign.total_clicks >= settings.alert_threshold_visits:
            send_campaign_alert(
                campaign,
                f"Campaign '{campaign.campaign_name}' has reached {campaign.total_clicks} clicks"
            )
            
        # Check conversion rate threshold
        if campaign.conversion_rate >= settings.alert_threshold_conversion_rate:
            send_campaign_alert(
                campaign,
                f"Campaign '{campaign.campaign_name}' has {campaign.conversion_rate}% conversion rate"
            )

def send_campaign_alert(campaign, message):
    """Send alert for campaign"""
    settings = frappe.get_single("TrackFlow Settings")
    
    # Get recipients
    recipients = []
    for recipient in settings.notification_recipients:
        if recipient.user:
            recipients.append(recipient.user)
            
    if not recipients:
        return
        
    # Create notification
    for user in recipients:
        notification = frappe.new_doc("Notification Log")
        notification.for_user = user
        notification.from_user = "Administrator"
        notification.subject = message
        notification.document_type = "Campaign"
        notification.document_name = campaign.name
        notification.insert(ignore_permissions=True)
        
    # Send email if configured
    if frappe.db.get_single_value("TrackFlow Settings", "send_email_notifications"):
        frappe.sendmail(
            recipients=recipients,
            subject=f"TrackFlow Alert: {message}",
            message=f"""
            <p>Hello,</p>
            <p>{message}</p>
            <p><a href="{frappe.utils.get_url()}/app/campaign/{campaign.name}">View Campaign</a></p>
            <p>Best regards,<br>TrackFlow</p>
            """
        )

def send_weekly_report():
    """Send weekly analytics report"""
    # This is a placeholder for weekly report functionality
    pass
