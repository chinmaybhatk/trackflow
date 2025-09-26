import frappe
from frappe import _
from trackflow.trackflow.utils import create_click_event, generate_visitor_id

no_cache = 1

def before_request():
    """Hook called before each request - used for tracking setup"""
    # This function is called by Frappe before processing any request
    # We can use it to set up tracking context if needed
    pass

def get_context(context):
    """Handle redirect for tracked links"""
    # Get tracking ID from path
    path_parts = frappe.request.path.strip('/').split('/')
    
    if len(path_parts) < 2:
        frappe.throw(_("Invalid tracking link"), frappe.DoesNotExistError)
    
    # Extract the short code from the path (usually the last part)
    tracking_id = path_parts[-1]
    
    # Get the tracked link
    tracked_link = frappe.db.get_value(
        "Tracked Link",
        {"short_code": tracking_id, "status": "Active"},
        ["name", "target_url", "campaign", "source", "medium", "custom_metadata"],
        as_dict=True
    )
    
    if not tracked_link:
        frappe.throw(_("Link not found or expired"), frappe.DoesNotExistError)
    
    # Get complete tracked link document
    tracked_link_doc = frappe.get_doc("Tracked Link", tracked_link.name)
    
    # Check if link has expired
    if tracked_link_doc.expiry_date and frappe.utils.get_datetime(tracked_link_doc.expiry_date) < frappe.utils.now_datetime():
        # Mark as expired
        tracked_link_doc.status = "Expired"
        tracked_link_doc.save(ignore_permissions=True)
        frappe.throw(_("Link has expired"), frappe.DoesNotExistError)
    
    # Track the click
    try:
        # Get visitor ID from cookie or create new (using consistent cookie name)
        visitor_id = frappe.request.cookies.get("trackflow_visitor")
        
        if not visitor_id:
            visitor_id = generate_visitor_id()
            
            # Set visitor cookie
            cookie_options = {
                'max_age': 31536000,  # 1 year
                'path': '/',
                'secure': frappe.request.is_secure,
                'httponly': True,
                'samesite': 'Lax'
            }
            
            frappe.local.cookie_manager.set_cookie(
                'trackflow_visitor', 
                visitor_id,
                **cookie_options
            )
        
        # Gather request data
        request_data = {
            "ip": frappe.local.request_ip or frappe.request.environ.get('REMOTE_ADDR'),
            "user_agent": frappe.request.headers.get("User-Agent", ""),
            "referrer": frappe.request.headers.get("Referer", "")
        }
        
        # Create click event
        click_event = create_click_event(tracked_link_doc, visitor_id, request_data)
        
        # Update click metrics on the tracked link
        frappe.db.sql("""
            UPDATE `tabTracked Link` 
            SET 
                click_count = IFNULL(click_count, 0) + 1,
                last_clicked = %s
            WHERE name = %s
        """, (frappe.utils.now(), tracked_link_doc.name))
        
        # Update unique visitors if this is a new visitor
        if not frappe.db.exists("Click Event", {"tracked_link": tracked_link_doc.name, "visitor_id": visitor_id, "name": ["!=", click_event.name]}):
            frappe.db.sql("""
                UPDATE `tabTracked Link` 
                SET unique_visitors = IFNULL(unique_visitors, 0) + 1
                WHERE name = %s
            """, tracked_link_doc.name)
        
        frappe.db.commit()
        
    except Exception as e:
        # Log error but don't prevent redirect
        frappe.log_error(frappe.get_traceback(), "Click Event Tracking Error")
    
    # Determine the final destination URL
    destination_url = tracked_link.target_url
    
    # If target URL is not specified, get from campaign
    if not destination_url and tracked_link.campaign:
        campaign = frappe.get_doc("Link Campaign", tracked_link.campaign)
        destination_url = campaign.target_url
    
    # If still no URL, show error
    if not destination_url:
        frappe.throw(_("Invalid destination URL"), frappe.ValidationError)
    
    # Apply UTM parameters if not already present
    from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
    
    parsed_url = urlparse(destination_url)
    params = parse_qs(parsed_url.query)
    
    # Add UTM parameters if not in URL already
    if tracked_link.campaign and 'utm_campaign' not in params:
        campaign = frappe.get_doc("Link Campaign", tracked_link.campaign)
        params['utm_campaign'] = [campaign.campaign_name]
    
    if tracked_link.source and 'utm_source' not in params:
        params['utm_source'] = [tracked_link.source]
    
    if tracked_link.medium and 'utm_medium' not in params:
        params['utm_medium'] = [tracked_link.medium]
    
    # Add visitor ID for cross-domain tracking
    if visitor_id:
        params['tf_visitor'] = [visitor_id]
    
    # Rebuild URL with parameters
    updated_query = urlencode(params, doseq=True)
    final_url = urlunparse((
        parsed_url.scheme,
        parsed_url.netloc,
        parsed_url.path,
        parsed_url.params,
        updated_query,
        parsed_url.fragment
    ))
    
    # Redirect to target URL
    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = final_url
