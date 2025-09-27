import frappe
from frappe import _
import uuid
import hashlib
import json
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs

def generate_visitor_id():
    """Generate a unique visitor ID"""
    return str(uuid.uuid4())

def generate_tracking_id():
    """Generate a unique tracking ID"""
    return hashlib.md5(str(uuid.uuid4()).encode()).hexdigest()[:8]

def get_visitor_from_request():
    """Get visitor ID from request (cookies or headers)"""
    visitor_id = None
    
    if frappe.request:
        # Check cookies - using consistent cookie name
        visitor_id = frappe.request.cookies.get('trackflow_visitor')
        
        # Check headers (for API requests)
        if not visitor_id:
            visitor_id = frappe.request.headers.get('X-TrackFlow-Visitor-ID')
    
    return visitor_id

def set_visitor_cookie(visitor_id):
    """Set visitor ID cookie"""
    if frappe.request:
        frappe.local.cookie_manager.set_cookie(
            'trackflow_visitor',
            visitor_id,
            max_age=31536000,  # 1 year
            httponly=True,
            samesite='Lax'
        )

def parse_utm_parameters(url):
    """Parse UTM parameters from URL"""
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    
    utm_params = {}
    utm_fields = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term']
    
    for field in utm_fields:
        if field in params:
            utm_params[field] = params[field][0]
    
    # Also check for tf_campaign parameter
    if 'tf_campaign' in params:
        utm_params['tf_campaign'] = params['tf_campaign'][0]
    
    return utm_params

def get_visitor_info_from_request():
    """Get visitor information from request"""
    info = {
        'ip_address': frappe.request.environ.get('REMOTE_ADDR') if frappe.request else None,
        'user_agent': frappe.request.environ.get('HTTP_USER_AGENT') if frappe.request else None,
        'referrer': frappe.request.environ.get('HTTP_REFERER') if frappe.request else None,
        'language': frappe.request.environ.get('HTTP_ACCEPT_LANGUAGE') if frappe.request else None
    }
    
    # Parse user agent
    if info['user_agent']:
        ua_info = parse_user_agent(info['user_agent'])
        info.update(ua_info)
    
    return info

def parse_user_agent(user_agent):
    """Parse user agent string to extract browser, OS, and device info"""
    info = {
        'browser': 'Unknown',
        'browser_version': None,
        'operating_system': 'Unknown',
        'device_type': 'Desktop'
    }
    
    ua_lower = user_agent.lower()
    
    # Detect browser
    if 'chrome' in ua_lower and 'edge' not in ua_lower:
        info['browser'] = 'Chrome'
    elif 'firefox' in ua_lower:
        info['browser'] = 'Firefox'
    elif 'safari' in ua_lower and 'chrome' not in ua_lower:
        info['browser'] = 'Safari'
    elif 'edge' in ua_lower:
        info['browser'] = 'Edge'
    elif 'opera' in ua_lower or 'opr' in ua_lower:
        info['browser'] = 'Opera'
    
    # Detect OS
    if 'windows' in ua_lower:
        info['operating_system'] = 'Windows'
    elif 'mac' in ua_lower:
        info['operating_system'] = 'macOS'
    elif 'linux' in ua_lower:
        info['operating_system'] = 'Linux'
    elif 'android' in ua_lower:
        info['operating_system'] = 'Android'
    elif 'ios' in ua_lower or 'iphone' in ua_lower or 'ipad' in ua_lower:
        info['operating_system'] = 'iOS'
    
    # Detect device type
    if 'mobile' in ua_lower or 'android' in ua_lower or 'iphone' in ua_lower:
        info['device_type'] = 'Mobile'
    elif 'tablet' in ua_lower or 'ipad' in ua_lower:
        info['device_type'] = 'Tablet'
    
    return info

def create_click_event(tracked_link, visitor_id, request_data=None):
    """Create a click event record for a tracked link"""
    try:
        # Get or create visitor
        visitor = None
        if frappe.db.exists("Visitor", {"visitor_id": visitor_id}):
            visitor = frappe.db.get_value("Visitor", {"visitor_id": visitor_id}, "name")
        else:
            # Create new visitor
            visitor_doc = frappe.new_doc("Visitor")
            visitor_doc.visitor_id = visitor_id
            visitor_doc.first_seen = frappe.utils.now()
            visitor_doc.last_seen = frappe.utils.now()
            
            if request_data:
                visitor_doc.ip_address = request_data.get("ip")
                visitor_doc.user_agent = request_data.get("user_agent")
                
                # Parse user agent
                if request_data.get("user_agent"):
                    ua_info = parse_user_agent(request_data.get("user_agent"))
                    visitor_doc.browser = ua_info.get("browser")
                    visitor_doc.operating_system = ua_info.get("operating_system")
                    visitor_doc.device_type = ua_info.get("device_type")
            
            visitor_doc.insert(ignore_permissions=True)
            visitor = visitor_doc.name
        
        # Create click event
        click_event = frappe.new_doc("Click Event")
        click_event.tracked_link = tracked_link.name
        click_event.visitor_id = visitor_id
        click_event.visitor = visitor
        click_event.click_time = frappe.utils.now()
        click_event.ip_address = request_data.get("ip") if request_data else None
        click_event.user_agent = request_data.get("user_agent") if request_data else None
        click_event.referrer = request_data.get("referrer") if request_data else None
        
        # Parse user agent for click event
        if request_data and request_data.get("user_agent"):
            ua_info = parse_user_agent(request_data.get("user_agent"))
            click_event.browser = ua_info.get("browser")
            click_event.operating_system = ua_info.get("operating_system")
            click_event.device_type = ua_info.get("device_type")
        
        # Get geo location if possible
        if request_data and request_data.get("ip"):
            try:
                from trackflow.utils.geo import get_geo_location
                geo = get_geo_location(request_data.get("ip"))
                if geo:
                    click_event.country = geo.get("country")
                    click_event.city = geo.get("city")
                    click_event.region = geo.get("region")
            except:
                # Geo location failed, continue without it
                pass
        
        click_event.insert(ignore_permissions=True)
        
        return click_event
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"Create Click Event Error: {str(e)}")
        raise

def calculate_attribution(deal_name, model='last_touch'):
    """Calculate attribution for a deal based on the selected model"""
    attributions = []
    
    # Get all touchpoints for the deal
    deal_link = frappe.db.get_value(
        "Deal Link Association",
        {"deal": deal_name},
        ["visitor_id", "lead"],
        as_dict=1
    )
    
    if not deal_link or not deal_link.visitor_id:
        return attributions
    
    # Get all sessions for the visitor
    sessions = frappe.get_all(
        "Visitor Session",
        filters={"visitor_id": deal_link.visitor_id},
        fields=["name", "visit_date", "utm_source", "utm_medium", "utm_campaign", "campaign"],
        order_by="visit_date"
    )
    
    if not sessions:
        return attributions
    
    # Get deal value
    deal_value = frappe.db.get_value("Opportunity", deal_name, "opportunity_amount") or 0
    
    if model == 'last_touch':
        # Give 100% credit to the last touchpoint
        last_session = sessions[-1]
        if last_session.campaign:
            attributions.append({
                "campaign": last_session.campaign,
                "attribution_percentage": 100,
                "attribution_value": deal_value
            })
    
    elif model == 'first_touch':
        # Give 100% credit to the first touchpoint
        first_session = sessions[0]
        if first_session.campaign:
            attributions.append({
                "campaign": first_session.campaign,
                "attribution_percentage": 100,
                "attribution_value": deal_value
            })
    
    elif model == 'linear':
        # Distribute credit equally among all touchpoints
        campaigns = [s.campaign for s in sessions if s.campaign]
        unique_campaigns = list(set(campaigns))
        
        if unique_campaigns:
            percentage = 100 / len(unique_campaigns)
            value = deal_value / len(unique_campaigns)
            
            for campaign in unique_campaigns:
                attributions.append({
                    "campaign": campaign,
                    "attribution_percentage": percentage,
                    "attribution_value": value
                })
    
    elif model == 'time_decay':
        # Give more credit to recent touchpoints
        campaigns = [(s.campaign, s.visit_date) for s in sessions if s.campaign]
        
        if campaigns:
            # Calculate days from first touch
            first_date = campaigns[0][1]
            weights = []
            total_weight = 0
            
            for campaign, visit_date in campaigns:
                days_diff = (visit_date - first_date).days
                weight = 2 ** (days_diff / 7)  # Double weight every week
                weights.append((campaign, weight))
                total_weight += weight
            
            # Group by campaign and sum weights
            campaign_weights = {}
            for campaign, weight in weights:
                if campaign not in campaign_weights:
                    campaign_weights[campaign] = 0
                campaign_weights[campaign] += weight
            
            # Calculate attribution
            for campaign, weight in campaign_weights.items():
                percentage = (weight / total_weight) * 100
                value = (weight / total_weight) * deal_value
                
                attributions.append({
                    "campaign": campaign,
                    "attribution_percentage": round(percentage, 2),
                    "attribution_value": round(value, 2)
                })
    
    elif model == 'position_based':
        # 40% to first touch, 40% to last touch, 20% distributed among middle
        campaigns = [s.campaign for s in sessions if s.campaign]
        
        if len(campaigns) == 1:
            attributions.append({
                "campaign": campaigns[0],
                "attribution_percentage": 100,
                "attribution_value": deal_value
            })
        elif len(campaigns) == 2:
            # 50% each
            for idx, campaign in enumerate(campaigns):
                attributions.append({
                    "campaign": campaign,
                    "attribution_percentage": 50,
                    "attribution_value": deal_value / 2
                })
        else:
            # First touch: 40%
            attributions.append({
                "campaign": campaigns[0],
                "attribution_percentage": 40,
                "attribution_value": deal_value * 0.4
            })
            
            # Middle touches: 20% distributed
            middle_campaigns = campaigns[1:-1]
            if middle_campaigns:
                middle_percentage = 20 / len(middle_campaigns)
                middle_value = (deal_value * 0.2) / len(middle_campaigns)
                
                for campaign in middle_campaigns:
                    attributions.append({
                        "campaign": campaign,
                        "attribution_percentage": middle_percentage,
                        "attribution_value": middle_value
                    })
            
            # Last touch: 40%
            attributions.append({
                "campaign": campaigns[-1],
                "attribution_percentage": 40,
                "attribution_value": deal_value * 0.4
            })
    
    return attributions

def get_campaign_roi(campaign_name):
    """Calculate ROI for a campaign"""
    campaign = frappe.get_doc("Link Campaign", campaign_name)
    
    # Get total revenue attributed to campaign
    revenue = frappe.db.sql("""
        SELECT COALESCE(SUM(attribution_value), 0) as total
        FROM `tabDeal Attribution`
        WHERE campaign = %s
        AND docstatus < 2
    """, campaign_name)[0][0]
    
    # Get campaign cost
    cost = campaign.budget_amount or 0
    
    # Calculate ROI
    if cost > 0:
        roi = ((revenue - cost) / cost) * 100
    else:
        roi = 0 if revenue == 0 else 100
    
    return {
        "revenue": revenue,
        "cost": cost,
        "roi": round(roi, 2),
        "profit": revenue - cost
    }

def format_currency(amount, currency=None):
    """Format amount as currency"""
    if not currency:
        currency = frappe.defaults.get_global_default("currency") or "USD"
    
    return frappe.utils.fmt_money(amount, currency=currency)

def get_date_range_filter(period):
    """Get date range filter based on period"""
    today = frappe.utils.today()
    
    if period == "today":
        from_date = today
        to_date = today
    elif period == "yesterday":
        from_date = frappe.utils.add_days(today, -1)
        to_date = frappe.utils.add_days(today, -1)
    elif period == "this_week":
        from_date = frappe.utils.get_first_day_of_week(today)
        to_date = today
    elif period == "last_week":
        from_date = frappe.utils.add_days(frappe.utils.get_first_day_of_week(today), -7)
        to_date = frappe.utils.add_days(from_date, 6)
    elif period == "this_month":
        from_date = frappe.utils.get_first_day(today)
        to_date = today
    elif period == "last_month":
        from_date = frappe.utils.add_months(frappe.utils.get_first_day(today), -1)
        to_date = frappe.utils.add_days(frappe.utils.get_first_day(today), -1)
    elif period == "this_quarter":
        from_date = frappe.utils.get_quarter_start(today)
        to_date = today
    elif period == "last_quarter":
        from_date = frappe.utils.add_months(frappe.utils.get_quarter_start(today), -3)
        to_date = frappe.utils.add_days(frappe.utils.get_quarter_start(today), -1)
    elif period == "this_year":
        from_date = frappe.utils.get_year_start(today)
        to_date = today
    elif period == "last_year":
        from_date = frappe.utils.add_years(frappe.utils.get_year_start(today), -1)
        to_date = frappe.utils.add_days(frappe.utils.get_year_start(today), -1)
    else:
        # Default to last 30 days
        from_date = frappe.utils.add_days(today, -30)
        to_date = today
    
    return {"from_date": from_date, "to_date": to_date}

# Jinja methods for templates
def jinja_methods():
    return {
        "get_tracking_script": get_tracking_script_tag,
        "get_campaign_url": get_campaign_tracking_url
    }

def jinja_filters():
    return {
        "format_visitor_id": lambda x: x[:8] + "..." if x and len(x) > 8 else x,
        "format_duration": format_duration
    }

def get_tracking_script_tag():
    """Get TrackFlow tracking script tag for templates"""
    return """<script src="{0}" async></script>""".format(
        frappe.utils.get_url("/api/method/trackflow.api.tracking.get_tracking_script")
    )

def get_campaign_tracking_url(url, campaign_name):
    """Get URL with campaign tracking parameters"""
    from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
    
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    
    # Add campaign parameter
    params['tf_campaign'] = [campaign_name]
    
    # Rebuild URL
    new_query = urlencode(params, doseq=True)
    return urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment
    ))

def format_duration(seconds):
    """Format duration in seconds to human readable format"""
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

def check_gdpr_consent(visitor_id):
    """Check if visitor has given GDPR consent"""
    if not visitor_id:
        return False
    
    visitor = frappe.db.get_value("Visitor", {"visitor_id": visitor_id}, ["gdpr_consent", "consent_date"], as_dict=1)
    
    if visitor and visitor.get("gdpr_consent"):
        return True
    
    return False

def record_gdpr_consent(visitor_id, consent_given=True, consent_text=None):
    """Record GDPR consent for a visitor"""
    if not visitor_id:
        return False
    
    visitor = frappe.db.get_value("Visitor", {"visitor_id": visitor_id}, "name")
    
    if visitor:
        frappe.db.set_value("Visitor", visitor, {
            "gdpr_consent": consent_given,
            "consent_date": frappe.utils.now(),
            "consent_text": consent_text or "Standard GDPR consent"
        })
        frappe.db.commit()
        return True
    
    return False

def anonymize_visitor_data(visitor_id):
    """Anonymize visitor data for GDPR compliance"""
    if not visitor_id:
        return False
    
    visitor = frappe.db.get_value("Visitor", {"visitor_id": visitor_id}, "name")
    
    if visitor:
        # Anonymize visitor data
        frappe.db.set_value("Visitor", visitor, {
            "ip_address": "0.0.0.0",
            "user_agent": "Anonymized",
            "gdpr_anonymized": 1,
            "anonymized_date": frappe.utils.now()
        })
        
        # Anonymize related events
        frappe.db.sql("""
            UPDATE `tabVisitor Event`
            SET ip_address = '0.0.0.0', user_agent = 'Anonymized'
            WHERE visitor = %s
        """, visitor)
        
        frappe.db.sql("""
            UPDATE `tabClick Event`
            SET ip_address = '0.0.0.0', user_agent = 'Anonymized'
            WHERE visitor = %s
        """, visitor)
        
        frappe.db.commit()
        return True
    
    return False
