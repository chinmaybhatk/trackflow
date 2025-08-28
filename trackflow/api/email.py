import frappe
from frappe import _
import base64
from bs4 import BeautifulSoup
from frappe.utils import now

# 1x1 transparent pixel GIF
PIXEL_GIF = "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"

@frappe.whitelist(allow_guest=True)
def track_email_open(campaign_id, recipient_id):
    """Track email opens via 1x1 pixel"""
    try:
        # Log email open
        log = frappe.new_doc("Email Campaign Log")
        log.campaign = campaign_id
        log.recipient = recipient_id
        log.action = "opened"
        log.timestamp = now()
        log.ip_address = frappe.local.request_ip
        log.user_agent = frappe.request.headers.get("User-Agent", "")
        
        # Get visitor ID if exists
        visitor_id = frappe.request.cookies.get("tf_visitor_id")
        if visitor_id:
            log.visitor_id = visitor_id
            
        log.insert(ignore_permissions=True)
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Email Open Tracking Error")
    
    # Return 1x1 transparent pixel
    frappe.response["type"] = "binary"
    frappe.response["filename"] = "pixel.gif"
    frappe.response["filecontent"] = base64.b64decode(PIXEL_GIF)
    frappe.response["content_type"] = "image/gif"

@frappe.whitelist(allow_guest=True)
def track_email_click(campaign_id, recipient_id, link_id):
    """Track email link clicks and redirect"""
    try:
        # Log email click
        log = frappe.new_doc("Email Campaign Log")
        log.campaign = campaign_id
        log.recipient = recipient_id
        log.action = "clicked"
        log.link_id = link_id
        log.timestamp = now()
        log.ip_address = frappe.local.request_ip
        
        visitor_id = frappe.request.cookies.get("tf_visitor_id")
        if visitor_id:
            log.visitor_id = visitor_id
            
        log.insert(ignore_permissions=True)
        
        # Get actual link URL
        link = frappe.get_doc("Tracked Link", link_id)
        target_url = link.target_url
        
        frappe.db.commit()
        
        # Redirect to target
        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = target_url
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Email Click Tracking Error")
        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = "/"

def wrap_email_links(html_content, campaign_id, recipient_id):
    """Wrap all links in email for tracking"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        for link in soup.find_all('a'):
            if 'href' not in link.attrs:
                continue
                
            original_url = link['href']
            
            # Skip unsubscribe and system links
            if 'unsubscribe' in original_url.lower() or 'mailto:' in original_url:
                continue
                
            # Create tracked link
            tracked_link = frappe.new_doc("Tracked Link")
            tracked_link.target_url = original_url
            tracked_link.campaign = campaign_id
            tracked_link.source = "email"
            tracked_link.medium = "email"
            tracked_link.is_active = 1
            tracked_link.insert(ignore_permissions=True)
            
            # Generate tracking URL
            track_url = f"{frappe.utils.get_url()}/api/method/trackflow.api.email.track_email_click"
            track_url += f"?campaign_id={campaign_id}&recipient_id={recipient_id}&link_id={tracked_link.name}"
            
            link['href'] = track_url
            
        return str(soup)
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Email Link Wrapping Error")
        return html_content

def add_tracking_pixel(html_content, campaign_id, recipient_id):
    """Add tracking pixel to email"""
    pixel_url = f"{frappe.utils.get_url()}/api/method/trackflow.api.email.track_email_open"
    pixel_url += f"?campaign_id={campaign_id}&recipient_id={recipient_id}"
    
    pixel_html = f'<img src="{pixel_url}" width="1" height="1" style="display:none;" />'
    
    # Add before closing body tag
    if '</body>' in html_content:
        return html_content.replace('</body>', f'{pixel_html}</body>')
    else:
        return html_content + pixel_html

@frappe.whitelist()
def prepare_tracked_email(subject, content, recipients, campaign_name):
    """Prepare email with tracking"""
    try:
        # Create or get campaign
        if not frappe.db.exists("Campaign", campaign_name):
            campaign = frappe.new_doc("Campaign")
            campaign.campaign_name = campaign_name
            campaign.campaign_type = "Email"
            campaign.start_date = frappe.utils.nowdate()
            campaign.status = "Active"
            campaign.insert()
        else:
            campaign = frappe.get_doc("Campaign", campaign_name)
            
        tracked_emails = []
        
        for recipient in recipients:
            # Generate unique recipient ID
            import hashlib
            recipient_id = hashlib.md5(f"{campaign.name}_{recipient}".encode()).hexdigest()[:8]
            
            # Wrap links and add pixel
            tracked_content = wrap_email_links(content, campaign.name, recipient_id)
            tracked_content = add_tracking_pixel(tracked_content, campaign.name, recipient_id)
            
            tracked_emails.append({
                "recipient": recipient,
                "subject": subject,
                "content": tracked_content
            })
            
        return {
            "status": "success",
            "campaign": campaign.name,
            "emails": tracked_emails
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Prepare Tracked Email Error")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_email_campaign_stats(campaign):
    """Get email campaign statistics"""
    try:
        stats = frappe.db.sql("""
            SELECT 
                action,
                COUNT(*) as count,
                COUNT(DISTINCT recipient) as unique_recipients
            FROM `tabEmail Campaign Log`
            WHERE campaign = %s
            GROUP BY action
        """, campaign, as_dict=True)
        
        result = {
            "sent": 0,
            "opened": 0,
            "clicked": 0,
            "open_rate": 0,
            "click_rate": 0
        }
        
        for stat in stats:
            if stat.action == "sent":
                result["sent"] = stat.count
            elif stat.action == "opened":
                result["opened"] = stat.unique_recipients
            elif stat.action == "clicked":
                result["clicked"] = stat.unique_recipients
                
        # Calculate rates
        if result["sent"] > 0:
            result["open_rate"] = (result["opened"] / result["sent"] * 100)
            result["click_rate"] = (result["clicked"] / result["sent"] * 100)
            
        return result
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Email Stats Error")
        return {}
