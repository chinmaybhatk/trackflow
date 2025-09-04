import frappe
from frappe import _
import json
from trackflow.utils import (
    generate_visitor_id, 
    generate_short_code, 
    get_visitor_from_request, 
    update_visitor_profile, 
    generate_qr_code_data_url,
    sanitize_url
)

@frappe.whitelist(allow_guest=True)
def track_event():
    """Track custom events from frontend"""
    try:
        data = json.loads(frappe.request.data)
        
        # Validate request data
        if not data:
            return {
                "status": "error", 
                "message": "No data provided"
            }
        
        # Get or create visitor
        visitor_id = data.get("visitor_id") or frappe.request.cookies.get("trackflow_visitor")
        
        if not visitor_id:
            visitor_id = generate_visitor_id()
            
            # Set cookie (will happen after response is processed)
            cookie_options = {
                'expires': (frappe.utils.datetime.datetime.now() + frappe.utils.datetime.timedelta(days=365)).strftime('%a, %d %b %Y %H:%M:%S GMT'),
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
            
        # Sanitize event data
        event_type = data.get("event_type", "pageview")
        url = sanitize_url(data.get("url", ""))
        referrer = sanitize_url(data.get("referrer", ""))
        properties = data.get("properties", {})
        
        # Create visitor if not exists
        if not frappe.db.exists("Visitor", {"visitor_id": visitor_id}):
            visitor = frappe.new_doc("Visitor")
            visitor.visitor_id = visitor_id
            visitor.first_seen = frappe.utils.now()
            visitor.last_seen = frappe.utils.now()
            visitor.ip_address = frappe.local.request_ip
            visitor.user_agent = frappe.request.headers.get('User-Agent', '')
            
            # Parse user agent for browser info
            from trackflow.utils import parse_user_agent
            browser, os = parse_user_agent(frappe.request.headers.get('User-Agent', ''))
            visitor.browser = browser
            visitor.operating_system = os
            
            # Determine device type
            if 'Mobile' in frappe.request.headers.get('User-Agent', '') or 'Android' in frappe.request.headers.get('User-Agent', ''):
                visitor.device_type = 'Mobile'
            elif 'iPad' in frappe.request.headers.get('User-Agent', '') or 'Tablet' in frappe.request.headers.get('User-Agent', ''):
                visitor.device_type = 'Tablet'
            else:
                visitor.device_type = 'Desktop'
                
            # Get geo location
            from trackflow.utils import get_geo_location
            geo = get_geo_location(frappe.local.request_ip)
            visitor.country = geo.get("country")
            visitor.city = geo.get("city")
                
            # Initialize counters
            visitor.total_page_views = 0
            visitor.total_sessions = 0
            visitor.total_clicks = 0
            visitor.engagement_score = 0
            
            # Save visitor
            visitor.insert(ignore_permissions=True)
        
        # Create event record using Visitor Event DocType
        event = frappe.new_doc("Visitor Event")
        event.visitor = frappe.get_value("Visitor", {"visitor_id": visitor_id}, "name")
        event.event_type = event_type
        event.event_category = properties.get("category", "custom")
        event.url = url
        event.referrer = referrer
        event.timestamp = frappe.utils.now()
        event.event_data = json.dumps(properties)
        event.ip_address = frappe.local.request_ip
        event.user_agent = frappe.request.headers.get('User-Agent', '')
        
        # Get UTM parameters
        event.utm_source = data.get("utm_source") or properties.get("utm_source")
        event.utm_medium = data.get("utm_medium") or properties.get("utm_medium")
        event.utm_campaign = data.get("utm_campaign") or properties.get("utm_campaign")
        event.utm_content = data.get("utm_content") or properties.get("utm_content")
        event.utm_term = data.get("utm_term") or properties.get("utm_term")
        
        # Insert event
        event.insert(ignore_permissions=True)
        
        # Update visitor's last seen time
        frappe.db.set_value("Visitor", {"visitor_id": visitor_id}, "last_seen", frappe.utils.now())
        
        # Update page view count for pageview events
        if event_type == "pageview":
            frappe.db.sql("""
                UPDATE `tabVisitor`
                SET total_page_views = IFNULL(total_page_views, 0) + 1
                WHERE visitor_id = %s
            """, visitor_id)
        
        # Update visitor session if it exists
        session_id = frappe.request.cookies.get("trackflow_session")
        if session_id and frappe.db.exists("Visitor Session", {"session_id": session_id}):
            frappe.db.set_value("Visitor Session", {"session_id": session_id}, "last_activity", frappe.utils.now())
            
            # For pageview events, increment session page views
            if event_type == "pageview":
                frappe.db.sql("""
                    UPDATE `tabVisitor Session`
                    SET page_views = IFNULL(page_views, 0) + 1
                    WHERE session_id = %s
                """, session_id)
        
        # Commit the transaction
        frappe.db.commit()
        
        return {
            "status": "success", 
            "visitor_id": visitor_id,
            "event_id": event.name
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "TrackFlow Event Tracking Error")
        return {"status": "error", "message": str(e)}


@frappe.whitelist(allow_guest=True)
def get_tracking_script():
    """Get tracking JavaScript code"""
    try:
        settings = frappe.get_single("TrackFlow Settings")
        
        if not settings or not settings.enable_tracking:
            return "<!-- TrackFlow tracking disabled -->"
            
        from trackflow.utils import get_tracking_script
        return get_tracking_script()
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "TrackFlow Script Generation Error")
        return "<!-- TrackFlow Error: Could not generate tracking script -->"


@frappe.whitelist()
def create_tracked_link(target_url, campaign=None, source=None, medium=None, term=None, content=None, custom_identifier=None, expiry_days=None):
    """Create a new tracked link"""
    try:
        # Validate URL
        if not target_url:
            frappe.throw(_("Target URL is required"))
            
        # Clean URL for security
        target_url = sanitize_url(target_url)
        
        # Validate campaign if provided
        if campaign and not frappe.db.exists("Link Campaign", campaign):
            frappe.throw(_("Invalid campaign"))
        
        # Generate short code
        short_code = generate_short_code()
        
        # Build URL with UTM parameters
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        
        parsed = urlparse(target_url)
        params = parse_qs(parsed.query)
        
        # Add UTM parameters
        if campaign:
            campaign_doc = frappe.get_doc("Link Campaign", campaign)
            params['utm_campaign'] = [campaign_doc.campaign_name]
            
            # Use campaign defaults if not specified
            if not source and campaign_doc.default_source:
                source = campaign_doc.default_source
                
            if not medium and campaign_doc.default_medium:
                medium = campaign_doc.default_medium
        
        if source:
            params['utm_source'] = [source]
        if medium:
            params['utm_medium'] = [medium]
        if term:
            params['utm_term'] = [term]
        if content:
            params['utm_content'] = [content]
            
        # Rebuild URL
        query = urlencode(params, doseq=True)
        final_url = urlunparse(parsed._replace(query=query))
        
        # Create tracked link
        link = frappe.new_doc("Tracked Link")
        link.short_code = short_code
        link.campaign = campaign
        link.custom_identifier = custom_identifier
        link.target_url = final_url
        link.source = source
        link.medium = medium
        link.status = "Active"
        link.created_by_user = frappe.session.user
        
        # Set expiry date if specified
        if expiry_days:
            link.expiry_date = frappe.utils.add_days(frappe.utils.now(), int(expiry_days))
        
        # Initialize metrics
        link.click_count = 0
        link.unique_visitors = 0
        
        link.insert()
        
        # Generate short URL
        short_url = f"{frappe.utils.get_url()}/r/{link.short_code}"
        
        # Generate QR code if possible
        qr_code_data = generate_qr_code_data_url(short_url)
        
        return {
            "status": "success",
            "name": link.name,
            "short_code": link.short_code,
            "short_url": short_url,
            "target_url": final_url,
            "qr_code": qr_code_data
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "TrackFlow Create Link Error")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_link_stats(tracking_id=None, link_name=None):
    """Get statistics for a tracked link"""
    try:
        # Get link by name or tracking ID
        if link_name:
            if not frappe.db.exists("Tracked Link", link_name):
                return {"status": "error", "message": "Link not found"}
            link = frappe.get_doc("Tracked Link", link_name)
        elif tracking_id:
            if not frappe.db.exists("Tracked Link", {"short_code": tracking_id}):
                return {"status": "error", "message": "Link not found"}
            link = frappe.get_doc("Tracked Link", {"short_code": tracking_id})
        else:
            return {"status": "error", "message": "Either tracking_id or link_name is required"}
        
        # Get click data
        clicks = frappe.db.sql("""
            SELECT 
                COUNT(*) as total_clicks,
                COUNT(DISTINCT visitor_id) as unique_visitors,
                COUNT(DISTINCT DATE(creation)) as days_active,
                MIN(creation) as first_click,
                MAX(creation) as last_click
            FROM `tabClick Event`
            WHERE tracked_link = %s
        """, link.name, as_dict=True)[0]
        
        # Get conversion data
        conversions = frappe.db.sql("""
            SELECT
                COUNT(*) as total_conversions,
                SUM(conversion_value) as total_value
            FROM `tabConversion`
            WHERE tracked_link = %s
        """, link.name, as_dict=True)[0]
        
        # Get geographic data
        geo_data = frappe.db.sql("""
            SELECT 
                country,
                COUNT(*) as clicks
            FROM `tabClick Event`
            WHERE tracked_link = %s AND country IS NOT NULL AND country != ''
            GROUP BY country
            ORDER BY clicks DESC
            LIMIT 10
        """, link.name, as_dict=True)
        
        # Get device data
        device_data = frappe.db.sql("""
            SELECT 
                device_type,
                COUNT(*) as clicks
            FROM `tabClick Event`
            WHERE tracked_link = %s
            GROUP BY device_type
            ORDER BY clicks DESC
        """, link.name, as_dict=True)
        
        # Get browser data
        browser_data = frappe.db.sql("""
            SELECT 
                browser,
                COUNT(*) as clicks
            FROM `tabClick Event`
            WHERE tracked_link = %s AND browser IS NOT NULL AND browser != ''
            GROUP BY browser
            ORDER BY clicks DESC
            LIMIT 5
        """, link.name, as_dict=True)
        
        # Get referrer data
        referrer_data = frappe.db.sql("""
            SELECT 
                referrer,
                COUNT(*) as clicks
            FROM `tabClick Event`
            WHERE tracked_link = %s AND referrer IS NOT NULL AND referrer != ''
            GROUP BY referrer
            ORDER BY clicks DESC
            LIMIT 10
        """, link.name, as_dict=True)
        
        # Generate click trend data
        trend_data = frappe.db.sql("""
            SELECT 
                DATE(creation) as date,
                COUNT(*) as clicks
            FROM `tabClick Event`
            WHERE 
                tracked_link = %s 
                AND creation >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            GROUP BY DATE(creation)
            ORDER BY date
        """, link.name, as_dict=True)
        
        # Calculate conversion rate
        conversion_rate = 0
        if clicks.total_clicks and conversions.total_conversions:
            conversion_rate = (conversions.total_conversions / clicks.total_clicks) * 100
        
        return {
            "status": "success",
            "link_info": {
                "name": link.name,
                "short_code": link.short_code,
                "short_url": f"{frappe.utils.get_url()}/r/{link.short_code}",
                "target_url": link.target_url,
                "campaign": link.campaign,
                "status": link.status,
                "created": str(link.creation),
                "expiry_date": str(link.expiry_date) if link.expiry_date else None
            },
            "stats": {
                "total_clicks": clicks.total_clicks or 0,
                "unique_visitors": clicks.unique_visitors or 0,
                "days_active": clicks.days_active or 0,
                "conversions": conversions.total_conversions or 0,
                "conversion_rate": round(conversion_rate, 2),
                "conversion_value": conversions.total_value or 0,
                "first_click": str(clicks.first_click) if clicks.first_click else None,
                "last_click": str(clicks.last_click) if clicks.last_click else None
            },
            "geography": geo_data,
            "devices": device_data,
            "browsers": browser_data,
            "referrers": referrer_data,
            "trend_data": trend_data
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "TrackFlow Get Stats Error")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def track_conversion(visitor_id, tracked_link=None, conversion_type=None, conversion_value=None, metadata=None):
    """Track a conversion event"""
    try:
        # Validate inputs
        if not visitor_id:
            return {"status": "error", "message": "Visitor ID is required"}
            
        # Get visitor
        visitor_name = frappe.get_value("Visitor", {"visitor_id": visitor_id}, "name")
        if not visitor_name:
            return {"status": "error", "message": "Visitor not found"}
            
        # Parse metadata if it's a string
        if metadata and isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except:
                metadata = {"raw_data": metadata}
        
        # Create conversion record
        conversion = frappe.new_doc("Conversion")
        conversion.visitor = visitor_name
        conversion.conversion_type = conversion_type or "general"
        
        if tracked_link:
            conversion.tracked_link = tracked_link
            
        if conversion_value:
            try:
                conversion.conversion_value = float(conversion_value)
            except:
                conversion.conversion_value = 0
                
        conversion.conversion_date = frappe.utils.now()
        
        # Add metadata
        if metadata:
            conversion.source = metadata.get("source")
            conversion.medium = metadata.get("medium")
            conversion.campaign = metadata.get("campaign")
            conversion.metadata = frappe.as_json(metadata)
            
        conversion.insert(ignore_permissions=True)
        
        # Update visitor conversion status
        frappe.db.sql("""
            UPDATE `tabVisitor`
            SET 
                has_converted = 1,
                conversion_count = IFNULL(conversion_count, 0) + 1,
                last_conversion_date = %s
            WHERE name = %s
        """, (frappe.utils.now(), visitor_name))
        
        # If tracked link is provided, update its conversion status
        if tracked_link:
            frappe.db.sql("""
                UPDATE `tabClick Event`
                SET 
                    led_to_conversion = 1,
                    conversion_value = %s,
                    conversion_type = %s
                WHERE tracked_link = %s AND visitor_id = %s
                ORDER BY creation DESC
                LIMIT 1
            """, (conversion.conversion_value or 0, conversion_type or "general", tracked_link, visitor_id))
        
        frappe.db.commit()
        
        return {
            "status": "success",
            "conversion_id": conversion.name,
            "message": "Conversion tracked successfully"
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "TrackFlow Conversion Error")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def update_link_status(link_name, status):
    """Update status of a tracked link"""
    try:
        if not frappe.db.exists("Tracked Link", link_name):
            return {"status": "error", "message": "Link not found"}
            
        if status not in ["Active", "Inactive", "Expired"]:
            return {"status": "error", "message": "Invalid status"}
        
        frappe.db.set_value("Tracked Link", link_name, "status", status)
        frappe.db.commit()
        
        return {
            "status": "success",
            "message": f"Link status updated to {status}"
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "TrackFlow Update Status Error")
        return {"status": "error", "message": str(e)}
