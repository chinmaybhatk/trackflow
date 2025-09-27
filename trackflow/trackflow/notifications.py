import frappe
from frappe import _
from frappe.utils import now_datetime, get_url, fmt_money

def send_goal_achieved_notification(goal):
    """Send notification when a campaign goal is achieved"""
    if not goal.notification_enabled:
        return
    
    campaign = frappe.get_doc("Link Campaign", goal.campaign)
    
    # Get recipients
    recipients = get_notification_recipients(campaign)
    
    if not recipients:
        return
    
    # Prepare notification content
    subject = _("Campaign Goal Achieved: {0}").format(goal.goal_name)
    
    message = """
    <h3>Campaign Goal Achieved!</h3>
    <p>The following goal has been achieved for campaign <strong>{campaign}</strong>:</p>
    
    <table border="1" cellpadding="5">
        <tr>
            <td><strong>Goal Name:</strong></td>
            <td>{goal_name}</td>
        </tr>
        <tr>
            <td><strong>Metric:</strong></td>
            <td>{metric}</td>
        </tr>
        <tr>
            <td><strong>Target Value:</strong></td>
            <td>{target_value}</td>
        </tr>
        <tr>
            <td><strong>Achieved Value:</strong></td>
            <td>{current_value}</td>
        </tr>
        <tr>
            <td><strong>Achieved On:</strong></td>
            <td>{achieved_on}</td>
        </tr>
    </table>
    
    <p><a href="{url}">View Campaign Dashboard</a></p>
    """.format(
        campaign=campaign.name,
        goal_name=goal.goal_name,
        metric=goal.metric,
        target_value=format_metric_value(goal.metric, goal.target_value),
        current_value=format_metric_value(goal.metric, goal.current_value),
        achieved_on=frappe.utils.format_datetime(goal.achieved_on),
        url=get_url("/app/trackflow-dashboard")
    )
    
    # Send email notification
    frappe.sendmail(
        recipients=recipients,
        subject=subject,
        message=message,
        delayed=False
    )
    
    # Create system notification
    for recipient in recipients:
        notification = frappe.new_doc("Notification Log")
        notification.subject = subject
        notification.for_user = recipient
        notification.type = "Alert"
        notification.document_type = "Campaign Goal"
        notification.document_name = goal.name
        notification.insert(ignore_permissions=True)

def send_conversion_notification(conversion):
    """Send notification for important conversions"""
    campaign = frappe.get_doc("Link Campaign", conversion.campaign)
    
    # Only send for high-value conversions
    if conversion.conversion_type not in ["Lead Created", "Deal Created", "Deal Won"]:
        return
    
    recipients = get_notification_recipients(campaign)
    
    if not recipients:
        return
    
    subject = _("New {0} from Campaign: {1}").format(
        conversion.conversion_type,
        campaign.name
    )
    
    message = """
    <h3>New Conversion Alert</h3>
    <p>A new conversion has occurred for campaign <strong>{campaign}</strong>:</p>
    
    <table border="1" cellpadding="5">
        <tr>
            <td><strong>Conversion Type:</strong></td>
            <td>{conversion_type}</td>
        </tr>
        <tr>
            <td><strong>Visitor ID:</strong></td>
            <td>{visitor_id}</td>
        </tr>
        <tr>
            <td><strong>Source:</strong></td>
            <td>{source}</td>
        </tr>
        <tr>
            <td><strong>Medium:</strong></td>
            <td>{medium}</td>
        </tr>
        <tr>
            <td><strong>Conversion Time:</strong></td>
            <td>{conversion_time}</td>
        </tr>
    </table>
    """.format(
        campaign=campaign.name,
        conversion_type=conversion.conversion_type,
        visitor_id=conversion.visitor_id,
        source=conversion.utm_source or "Direct",
        medium=conversion.utm_medium or "None",
        conversion_time=frappe.utils.format_datetime(conversion.conversion_date)
    )
    
    if conversion.lead:
        message += """
        <p><strong>Lead Details:</strong></p>
        <table border="1" cellpadding="5">
            <tr>
                <td><strong>Name:</strong></td>
                <td>{lead_name}</td>
            </tr>
            <tr>
                <td><strong>Email:</strong></td>
                <td>{email}</td>
            </tr>
            <tr>
                <td><strong>Phone:</strong></td>
                <td>{phone}</td>
            </tr>
        </table>
        """.format(
            lead_name=conversion.lead_name,
            email=conversion.email_id or "N/A",
            phone=conversion.phone or "N/A"
        )
    
    if conversion.deal:
        deal = frappe.get_doc("Opportunity", conversion.deal)
        message += """
        <p><strong>Deal Details:</strong></p>
        <table border="1" cellpadding="5">
            <tr>
                <td><strong>Deal Name:</strong></td>
                <td>{deal_name}</td>
            </tr>
            <tr>
                <td><strong>Value:</strong></td>
                <td>{value}</td>
            </tr>
            <tr>
                <td><strong>Status:</strong></td>
                <td>{status}</td>
            </tr>
        </table>
        """.format(
            deal_name=deal.title,
            value=fmt_money(deal.opportunity_amount, currency=deal.currency),
            status=deal.status
        )
    
    message += '<p><a href="{url}">View Conversion Details</a></p>'.format(
        url=get_url(conversion.get_url())
    )
    
    # Send email notification
    frappe.sendmail(
        recipients=recipients,
        subject=subject,
        message=message,
        delayed=False
    )

def send_campaign_alert(campaign, alert_type, message_details):
    """Send various campaign alerts"""
    recipients = get_notification_recipients(campaign)
    
    if not recipients:
        return
    
    alert_configs = {
        "low_performance": {
            "subject": _("Low Performance Alert: {0}").format(campaign.name),
            "message": """
            <h3>Campaign Performance Alert</h3>
            <p>Campaign <strong>{campaign}</strong> is performing below expectations:</p>
            {details}
            <p><a href="{url}">View Campaign Dashboard</a></p>
            """
        },
        "budget_exceeded": {
            "subject": _("Budget Alert: {0}").format(campaign.name),
            "message": """
            <h3>Campaign Budget Alert</h3>
            <p>Campaign <strong>{campaign}</strong> has exceeded its budget:</p>
            {details}
            <p><a href="{url}">View Campaign Details</a></p>
            """
        },
        "campaign_ended": {
            "subject": _("Campaign Ended: {0}").format(campaign.name),
            "message": """
            <h3>Campaign Completed</h3>
            <p>Campaign <strong>{campaign}</strong> has ended.</p>
            {details}
            <p><a href="{url}">View Final Report</a></p>
            """
        }
    }
    
    if alert_type not in alert_configs:
        return
    
    config = alert_configs[alert_type]
    
    message = config["message"].format(
        campaign=campaign.name,
        details=message_details,
        url=get_url("/app/trackflow-campaign/" + campaign.name)
    )
    
    # Send email
    frappe.sendmail(
        recipients=recipients,
        subject=config["subject"],
        message=message,
        delayed=False
    )
    
    # Create notification log
    for recipient in recipients:
        notification = frappe.new_doc("Notification Log")
        notification.subject = config["subject"]
        notification.for_user = recipient
        notification.type = "Alert"
        notification.document_type = "Link Campaign"
        notification.document_name = campaign.name
        notification.insert(ignore_permissions=True)

def get_notification_recipients(campaign):
    """Get list of users to notify for campaign events"""
    recipients = []
    
    # Add campaign owner
    if campaign.owner:
        recipients.append(campaign.owner)
    
    # Add campaign team members if defined
    if hasattr(campaign, 'team_members'):
        for member in campaign.team_members:
            if member.user and member.user not in recipients:
                recipients.append(member.user)
    
    # Add users with specific roles
    role_recipients = frappe.db.sql("""
        SELECT DISTINCT u.name
        FROM `tabUser` u
        INNER JOIN `tabHas Role` hr ON hr.parent = u.name
        WHERE hr.role IN ('Sales Manager', 'Marketing Manager')
        AND u.enabled = 1
        AND u.name NOT IN ('Administrator', 'Guest')
    """, as_dict=1)
    
    for user in role_recipients:
        if user.name not in recipients:
            recipients.append(user.name)
    
    # Filter out users who have disabled notifications
    final_recipients = []
    for recipient in recipients:
        user = frappe.get_doc("User", recipient)
        if user.enabled and not user.mute_emails:
            final_recipients.append(recipient)
    
    return final_recipients

def format_metric_value(metric, value):
    """Format metric value based on type"""
    if metric in ["Revenue", "Deal Value"]:
        return fmt_money(value, currency=frappe.defaults.get_global_default("currency"))
    elif metric in ["Conversion Rate", "Click Rate", "Bounce Rate"]:
        return "{0}%".format(value)
    else:
        return str(value)

def check_campaign_performance():
    """Scheduled job to check campaign performance and send alerts"""
    # Get active campaigns
    campaigns = frappe.get_all(
        "Link Campaign",
        filters={
            "status": "Active",
            "docstatus": ["<", 2]
        },
        fields=["name", "expected_conversions", "expected_revenue"]
    )
    
    for campaign in campaigns:
        doc = frappe.get_doc("Link Campaign", campaign.name)
        
        # Get current metrics
        conversions = frappe.db.count(
            "Link Conversion",
            filters={
                "campaign": campaign.name,
                "docstatus": ["<", 2]
            }
        )
        
        revenue = frappe.db.sql("""
            SELECT COALESCE(SUM(opportunity_amount), 0) as total
            FROM `tabOpportunity` o
            INNER JOIN `tabDeal Attribution` da ON da.deal = o.name
            WHERE da.campaign = %s
            AND o.status = 'Closed'
            AND o.docstatus < 2
        """, campaign.name)[0][0]
        
        # Check if performance is below expectations
        alerts = []
        
        if doc.expected_conversions and conversions < (doc.expected_conversions * 0.5):
            alerts.append(
                "Conversions are at {0} ({1}% of target)".format(
                    conversions,
                    round(conversions / doc.expected_conversions * 100, 1)
                )
            )
        
        if doc.expected_revenue and revenue < (doc.expected_revenue * 0.5):
            alerts.append(
                "Revenue is at {0} ({1}% of target)".format(
                    fmt_money(revenue),
                    round(revenue / doc.expected_revenue * 100, 1)
                )
            )
        
        if alerts:
            details = "<ul>"
            for alert in alerts:
                details += "<li>{0}</li>".format(alert)
            details += "</ul>"
            
            send_campaign_alert(doc, "low_performance", details)
