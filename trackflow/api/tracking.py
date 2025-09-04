import frappe
from frappe import _
import json
from trackflow.trackflow.utils import (
    generate_visitor_id, 
    get_visitor_from_request, 
    set_visitor_cookie,
    parse_user_agent,
    check_gdpr_consent,
    record_gdpr_consent
)
from trackflow.trackflow.utils.error_handler import (
    handle_error,
    validate_required_fields,
    validate_url,
    sanitize_input,
    get_client_ip,
    rate_limit_check,
    ValidationError,
    TrackingError
)

@frappe.whitelist(allow_guest=True)
@handle_error(error_type="Event Tracking")
def track_event():
    """Track custom events from frontend"""
    # Rate limiting
    client_ip = get_client_ip()
    allowed, remaining = rate_limit_check(f"track_event:{client_ip}", limit=1000, window=3600)
    
    if not allowed:
        raise TrackingError(_("Rate limit exceeded. Please try again later."), error_code="RATE_LIMIT_EXCEEDED")
    
    # Parse and sanitize request data
    data = json.loads(frappe.request.data or '{}')
    data = sanitize_input(data, max_length=1000)
    
    # Validate request data
    if not data:
        raise ValidationError(_("No data provided"))
    
    # Get or create visitor
    visitor_id = data.get("visitor_id") or get_visitor_from_request()
    
    if not visitor_id:
        visitor_id = generate_visitor_id()
        set_visitor_cookie(visitor_id)
    
    # Check GDPR consent if enabled
    settings = frappe.get_single("TrackFlow Settings")
    if settings.require_gdpr_consent and not check_gdpr_consent(visitor_id):
        # Don't track without consent
        return {
            "status": "error",
            "error_code": "GDPR_CONSENT_REQUIRED",
            "message": _("User consent required for tracking")
        }
    
    # Sanitize event data
    event_type = data.get("event_type", "pageview")
    url = validate_url(data.get("url", "")) if data.get("url") else ""
    referrer = validate_url(data.get("referrer", "")) if data.get("referrer") else ""
    properties = data.get("properties", {})
    
    # Create or update visitor
    visitor = get_or_create_visitor(visitor_id, client_ip)
    
    # Create event record
    event = frappe.new_doc("Visitor Event")
    event.visitor = visitor
    event.event_type = event_type
    event.event_category = properties.get("category", "custom")
    event.url = url
    event.referrer = referrer
    event.timestamp = frappe.utils.now()
    event.event_data = json.dumps(properties)
    event.ip_address = client_ip
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
    frappe.db.set_value("Visitor", visitor, "last_seen", frappe.utils.now())
    
    # Update page view count for pageview events
    if event_type == "pageview":
        frappe.db.sql("""
            UPDATE `tabVisitor`
            SET total_page_views = IFNULL(total_page_views, 0) + 1
            WHERE name = %s
        """, visitor)
    
    # Update visitor session if it exists
    update_visitor_session(visitor_id, event_type)
    
    frappe.db.commit()
    
    return {
        "status": "success", 
        "visitor_id": visitor_id,
        "event_id": event.name,
        "remaining_requests": remaining
    }

def get_or_create_visitor(visitor_id, ip_address):
    """Get or create visitor record"""
    visitor_name = frappe.db.get_value("Visitor", {"visitor_id": visitor_id}, "name")
    
    if visitor_name:
        return visitor_name
    
    # Create new visitor
    visitor = frappe.new_doc("Visitor")
    visitor.visitor_id = visitor_id
    visitor.first_seen = frappe.utils.now()
    visitor.last_seen = frappe.utils.now()
    visitor.ip_address = ip_address
    visitor.user_agent = frappe.request.headers.get('User-Agent', '')
    
    # Parse user agent
    ua_info = parse_user_agent(visitor.user_agent)
    visitor.browser = ua_info.get('browser')
    visitor.operating_system = ua_info.get('operating_system')
    visitor.device_type = ua_info.get('device_type')
    
    # Get geo location
    try:
        from trackflow.utils.geo import get_geo_location
        geo = get_geo_location(ip_address)
        if geo:
            visitor.country = geo.get("country")
            visitor.city = geo.get("city")
    except:
        pass
    
    # Initialize counters
    visitor.total_page_views = 0
    visitor.total_sessions = 0
    visitor.total_clicks = 0
    visitor.engagement_score = 0
    
    visitor.insert(ignore_permissions=True)
    return visitor.name

def update_visitor_session(visitor_id, event_type):
    """Update visitor session if it exists"""
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

@frappe.whitelist(allow_guest=True)
@handle_error(error_type="Script Generation", return_response=False)
def get_tracking_script():
    """Get tracking JavaScript code"""
    settings = frappe.get_single("TrackFlow Settings")
    
    if not settings or not settings.enable_tracking:
        return "<!-- TrackFlow tracking disabled -->"
    
    # Generate tracking script
    script = """
(function() {
    var TrackFlow = window.TrackFlow || {};
    
    TrackFlow.apiUrl = '%s';
    TrackFlow.visitorId = '%s';
    TrackFlow.sessionId = '%s';
    TrackFlow.requireConsent = %s;
    
    TrackFlow.track = function(eventType, properties) {
        var data = {
            visitor_id: TrackFlow.visitorId,
            event_type: eventType || 'pageview',
            url: window.location.href,
            referrer: document.referrer,
            properties: properties || {},
            utm_source: getParam('utm_source'),
            utm_medium: getParam('utm_medium'),
            utm_campaign: getParam('utm_campaign'),
            utm_content: getParam('utm_content'),
            utm_term: getParam('utm_term')
        };
        
        fetch(TrackFlow.apiUrl + '/api/method/trackflow.api.tracking.track_event', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data),
            credentials: 'include'
        });
    };
    
    TrackFlow.consent = function(granted) {
        fetch(TrackFlow.apiUrl + '/api/method/trackflow.api.tracking.record_consent', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                visitor_id: TrackFlow.visitorId,
                consent_given: granted
            }),
            credentials: 'include'
        });
    };
    
    function getParam(name) {
        var match = RegExp('[?&]' + name + '=([^&]*)').exec(window.location.search);
        return match && decodeURIComponent(match[1].replace(/\+/g, ' '));
    }
    
    // Auto-track pageviews
    if (!TrackFlow.requireConsent || getCookie('trackflow_consent') === 'true') {
        TrackFlow.track('pageview');
    }
    
    function getCookie(name) {
        var value = "; " + document.cookie;
        var parts = value.split("; " + name + "=");
        if (parts.length == 2) return parts.pop().split(";").shift();
    }
    
    window.TrackFlow = TrackFlow;
})();
""" % (
        frappe.utils.get_url(),
        get_visitor_from_request() or "",
        frappe.request.cookies.get("trackflow_session") or "",
        "true" if settings.require_gdpr_consent else "false"
    )
    
    # Set content type
    frappe.response["content_type"] = "application/javascript"
    
    return script

@frappe.whitelist()
@handle_error(error_type="Create Link")
def create_tracked_link(**kwargs):
    """Create a new tracked link"""
    # Validate required fields
    validate_required_fields(kwargs, ["target_url"])
    
    # Validate and sanitize URL
    target_url = validate_url(kwargs.get("target_url"))
    
    # Validate campaign if provided
    campaign = kwargs.get("campaign")
    if campaign and not frappe.db.exists("Link Campaign", campaign):
        raise ValidationError(_("Invalid campaign"))
    
    # Generate short code
    from trackflow.utils import generate_short_code
    short_code = generate_short_code()
    
    # Create tracked link
    link = frappe.new_doc("Tracked Link")
    link.short_code = short_code
    link.campaign = campaign
    link.custom_identifier = kwargs.get("custom_identifier")
    link.target_url = target_url
    link.source = kwargs.get("source")
    link.medium = kwargs.get("medium")
    link.status = "Active"
    link.created_by_user = frappe.session.user
    
    # Set expiry date if specified
    expiry_days = kwargs.get("expiry_days")
    if expiry_days:
        link.expiry_date = frappe.utils.add_days(frappe.utils.now(), int(expiry_days))
    
    link.insert()
    
    # Generate response
    short_url = f"{frappe.utils.get_url()}/r/{link.short_code}"
    
    # Generate QR code if available
    qr_code_data = None
    try:
        from trackflow.utils import generate_qr_code_data_url
        qr_code_data = generate_qr_code_data_url(short_url)
    except:
        pass
    
    return {
        "status": "success",
        "name": link.name,
        "short_code": link.short_code,
        "short_url": short_url,
        "target_url": link.target_url,
        "qr_code": qr_code_data
    }

@frappe.whitelist()
@handle_error(error_type="Link Stats")
def get_link_stats(**kwargs):
    """Get statistics for a tracked link"""
    tracking_id = kwargs.get("tracking_id")
    link_name = kwargs.get("link_name")
    
    if not tracking_id and not link_name:
        raise ValidationError(_("Either tracking_id or link_name is required"))
    
    # Get link
    if link_name:
        if not frappe.db.exists("Tracked Link", link_name):
            raise ValidationError(_("Link not found"))
        link = frappe.get_doc("Tracked Link", link_name)
    else:
        link_name = frappe.db.get_value("Tracked Link", {"short_code": tracking_id}, "name")
        if not link_name:
            raise ValidationError(_("Link not found"))
        link = frappe.get_doc("Tracked Link", link_name)
    
    # Get statistics
    stats = get_link_statistics(link.name)
    
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
        "stats": stats
    }

def get_link_statistics(link_name):
    """Get detailed statistics for a link"""
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
    """, link_name, as_dict=True)[0]
    
    # Get conversion data
    conversions = frappe.db.sql("""
        SELECT
            COUNT(*) as total_conversions,
            SUM(conversion_value) as total_value
        FROM `tabConversion`
        WHERE tracked_link = %s
    """, link_name, as_dict=True)[0]
    
    # Calculate conversion rate
    conversion_rate = 0
    if clicks["total_clicks"] and conversions["total_conversions"]:
        conversion_rate = (conversions["total_conversions"] / clicks["total_clicks"]) * 100
    
    return {
        "total_clicks": clicks["total_clicks"] or 0,
        "unique_visitors": clicks["unique_visitors"] or 0,
        "days_active": clicks["days_active"] or 0,
        "conversions": conversions["total_conversions"] or 0,
        "conversion_rate": round(conversion_rate, 2),
        "conversion_value": conversions["total_value"] or 0,
        "first_click": str(clicks["first_click"]) if clicks["first_click"] else None,
        "last_click": str(clicks["last_click"]) if clicks["last_click"] else None
    }

@frappe.whitelist()
@handle_error(error_type="Track Conversion")
def track_conversion(**kwargs):
    """Track a conversion event"""
    # Validate required fields
    validate_required_fields(kwargs, ["visitor_id"])
    
    visitor_id = kwargs.get("visitor_id")
    
    # Get visitor
    visitor_name = frappe.db.get_value("Visitor", {"visitor_id": visitor_id}, "name")
    if not visitor_name:
        raise ValidationError(_("Visitor not found"))
    
    # Create conversion record
    conversion = frappe.new_doc("Conversion")
    conversion.visitor = visitor_name
    conversion.conversion_type = kwargs.get("conversion_type", "general")
    conversion.tracked_link = kwargs.get("tracked_link")
    conversion.conversion_value = float(kwargs.get("conversion_value", 0))
    conversion.conversion_date = frappe.utils.now()
    
    # Add metadata
    metadata = kwargs.get("metadata", {})
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
    
    frappe.db.commit()
    
    return {
        "status": "success",
        "conversion_id": conversion.name,
        "message": _("Conversion tracked successfully")
    }

@frappe.whitelist(allow_guest=True)
@handle_error(error_type="Record Consent")
def record_consent():
    """Record GDPR consent"""
    data = json.loads(frappe.request.data or '{}')
    
    visitor_id = data.get("visitor_id") or get_visitor_from_request()
    consent_given = data.get("consent_given", False)
    
    if not visitor_id:
        raise ValidationError(_("Visitor ID required"))
    
    # Record consent
    success = record_gdpr_consent(visitor_id, consent_given, data.get("consent_text"))
    
    # Set consent cookie
    if success and consent_given:
        frappe.local.cookie_manager.set_cookie(
            'trackflow_consent',
            'true',
            max_age=31536000,  # 1 year
            httponly=False,  # Allow JS access
            samesite='Lax'
        )
    
    return {
        "status": "success" if success else "error",
        "message": _("Consent recorded") if success else _("Failed to record consent")
    }
