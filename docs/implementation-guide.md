# TrackFlow Implementation Guide

## Quick Start Guide

TrackFlow supports two deployment scenarios:

### 🌐 **Scenario A: External Website Tracking** (Most Common)
- **TrackFlow Server**: Runs on your Frappe/CRM server  
- **Tracked Websites**: Any external website(s) with embedded JavaScript
- **Use Case**: Track marketing campaigns across multiple domains/sites while centralizing data in your CRM

### 🏠 **Scenario B: Same-Server Tracking** 
- **TrackFlow Server**: Runs on same Frappe server as your website
- **Tracked Website**: Same Frappe site with website builder
- **Use Case**: All-in-one Frappe setup with built-in website

> **💡 Recommendation**: Most users want **Scenario A** to track external WordPress/Shopify/custom websites while keeping attribution data in their Frappe CRM.

### Prerequisites
- **Frappe Framework**: v15.0+ 
- **Python**: 3.10+
- **Database**: MySQL 8.0+ or MariaDB 10.6+
- **Frappe CRM**: v2.0+ (for CRM integration)
- **Redis**: For caching and rate limiting (recommended)

### Installation

#### 1. Install TrackFlow App
```bash
# On Frappe Cloud or self-hosted
bench get-app https://github.com/chinmaybhatk/trackflow.git
bench install-app trackflow --site your-site.com

# Or via local development
cd frappe-bench/apps
git clone https://github.com/chinmaybhatk/trackflow.git
bench install-app trackflow
```

#### 2. Post-Installation Setup
```bash
# Run migrations to set up database schema
bench migrate --site your-site.com

# Clear cache to load new workspace
bench clear-cache --site your-site.com

# Restart to activate hooks
bench restart
```

#### 3. Verify Installation
1. **Check CRM Integration**: Log into Frappe CRM → Look for "TrackFlow Analytics" in sidebar below "Call Logs"
2. **Access Settings**: Go to `/app/trackflow-settings` → Should load without errors
3. **Test Campaign Creation**: Create a new Link Campaign → Generate tracked links

### Choose Your Tracking Scenario

#### 📋 **For External Website Tracking** (Recommended)
👉 **Continue to**: [External Site Tracking Guide](./external-site-tracking.md)

This guide covers:
- Cross-domain tracking setup
- JavaScript embed for any website (WordPress, Shopify, custom sites)
- Form integration and lead capture
- Multi-domain campaign tracking

#### 📋 **For Same-Server Tracking**
👉 **Continue below** for same-server implementation details

---

## Core Workflows

### 1. Campaign Creation & Link Generation

#### Step-by-Step Process
```python
# 1. Create Link Campaign
campaign = frappe.new_doc("Link Campaign")
campaign.campaign_name = "Q4 Email Marketing"
campaign.campaign_type = "Email Marketing"
campaign.source = "email"
campaign.medium = "newsletter"
campaign.budget = 5000.00
campaign.start_date = "2024-01-01"
campaign.end_date = "2024-03-31"
campaign.insert()

# 2. Generate Tracked Links
link = frappe.new_doc("Tracked Link")
link.title = "Product Demo CTA"
link.destination_url = "https://example.com/demo"
link.campaign = campaign.name
link.source = "email"
link.medium = "newsletter"
link.content = "header-cta"
link.insert()

# Result: Short URL like https://yoursite.com/r/abc123
```

#### Via UI (Recommended)
1. **Access TrackFlow**: CRM → TrackFlow Analytics → Campaigns
2. **Create Campaign**: Click "New" → Fill campaign details
3. **Generate Links**: Campaign → "Create Tracked Link" → Configure UTM parameters
4. **Get Assets**: Copy short URL + download QR code

### 2. Visitor Tracking Implementation

#### Automatic Tracking (Default)
TrackFlow automatically injects tracking JavaScript when `enable_tracking = True` in settings:

```html
<!-- Auto-injected by TrackFlow -->
<script src="/api/method/trackflow.api.tracking.get_tracking_script" async></script>
```

#### Manual JavaScript Integration
```javascript
// Custom event tracking
trackflow.track('page_view', {
    page: window.location.pathname,
    title: document.title,
    referrer: document.referrer
});

// Form submission tracking
document.getElementById('contact-form').addEventListener('submit', function(e) {
    trackflow.track('form_submit', {
        form_name: 'contact_form',
        campaign: trackflow.getCampaign(), // From URL parameters
        visitor_id: trackflow.getVisitorId()
    });
});

// Custom conversion events
trackflow.track('conversion', {
    type: 'demo_request',
    value: 100,
    campaign: trackflow.getCampaign()
});
```

### 3. CRM Lead Attribution

#### Automatic Attribution (Default Behavior)
When a visitor with tracking cookies fills a lead form:

```python
# Happens automatically via document hooks
def on_lead_create(doc, method):
    visitor_id = frappe.request.cookies.get('trackflow_visitor_id')
    
    if visitor_id:
        # Get visitor journey
        visitor = frappe.get_doc("Visitor", {"visitor_id": visitor_id})
        
        # Apply attribution
        doc.trackflow_visitor_id = visitor_id
        doc.trackflow_source = visitor.source
        doc.trackflow_medium = visitor.medium
        doc.trackflow_campaign = visitor.campaign
        doc.trackflow_first_touch_date = visitor.first_seen
        doc.trackflow_last_touch_date = visitor.last_seen
        doc.trackflow_touch_count = get_touch_count(visitor_id)
        
        # Create conversion record
        create_conversion(doc, visitor, "lead_created")
```

#### Manual Attribution
```python
# Link existing leads to visitors
@frappe.whitelist()
def link_visitor_to_lead(lead_name, visitor_id):
    result = frappe.call("trackflow.integrations.crm_lead.link_visitor_to_lead", 
                        lead=lead_name, 
                        visitor_id=visitor_id)
    return result
```

### 4. Attribution Models ✅ WORKING

#### Current Working Attribution (Production Ready)
```python
# TrackFlow automatically provides last-click attribution
# When a visitor fills a form → becomes a lead:

def on_lead_create(lead, method):
    visitor_id = lead.get('trackflow_visitor_id')
    if visitor_id:
        # Get visitor's campaign data
        visitor = frappe.get_doc("Visitor", {"visitor_id": visitor_id})
        
        # ✅ AUTOMATIC ATTRIBUTION - THIS IS WORKING NOW
        lead.trackflow_source = visitor.source        # "email", "google", "facebook"
        lead.trackflow_medium = visitor.medium        # "newsletter", "organic", "ads"  
        lead.trackflow_campaign = visitor.campaign    # "Q4-Email-Campaign"
        lead.trackflow_first_touch_date = visitor.first_seen
        lead.trackflow_last_touch_date = visitor.last_seen
```

#### Configure Attribution Settings
```python
# Via TrackFlow Settings - Basic configuration working
settings = frappe.get_single("TrackFlow Settings")
settings.default_attribution_model = "Last Touch"  # ✅ Working now
settings.attribution_window_days = 30               # ✅ Working now
settings.save()
```

#### Advanced Attribution Models (Future Enhancement)
```python
# ⏳ PLANNED: Advanced multi-touch attribution
# Current: Last-click attribution covers 90% of use cases

# Future: Custom attribution rules for complex B2B journeys
attribution_model = frappe.new_doc("Attribution Model")  
attribution_model.name = "Custom B2B Model"
attribution_model.model_type = "linear"  # Split credit across touches
attribution_model.description = "Equal credit to all touchpoints in journey"
# This will be implemented in Phase 3
```

#### What's Working Right Now ✅
```python
# Real example of current attribution in action:

# 1. Visitor clicks: yoursite.com/r/abc123 (from email campaign)
# 2. Visitor browses site, fills contact form  
# 3. CRM Lead created with attribution data:

lead = frappe.get_doc("CRM Lead", "LEAD-001")
print(f"Source: {lead.trackflow_source}")           # "email" 
print(f"Medium: {lead.trackflow_medium}")           # "newsletter"
print(f"Campaign: {lead.trackflow_campaign}")       # "Q4-Email-Campaign"
print(f"First Touch: {lead.trackflow_first_touch_date}")  # "2024-01-01 09:15:00"

# This gives you everything needed for ROI calculation! ✅
```

---

## API Reference

### Authentication
All API calls (except guest tracking) require authentication:

```python
# Session-based (via Frappe login)
headers = {"Cookie": "sid=your_session_id"}

# API Key authentication
headers = {"Authorization": "token your_api_key:your_api_secret"}
```

### Core Tracking APIs

#### 1. Link Redirection
```http
GET /r/{short_code}
# Automatically tracks click and redirects
# No authentication required
```

#### 2. Event Tracking
```python
# POST /api/method/trackflow.api.tracking.track_event
{
    "event_type": "page_view",
    "visitor_id": "v_abc123456789",
    "page_url": "https://example.com/products",
    "event_data": {
        "title": "Product Page",
        "category": "products"
    }
}
```

#### 3. Visitor Data
```python
# GET /api/method/trackflow.api.visitor.get_visitor_data
params = {"visitor_id": "v_abc123456789"}

# Response
{
    "status": "success",
    "data": {
        "visitor_id": "v_abc123456789",
        "first_seen": "2024-01-01 10:30:00",
        "last_seen": "2024-01-01 11:45:00",
        "page_views": 5,
        "sessions": [...],
        "clicks": [...],
        "conversions": [...]
    }
}
```

### Campaign Management APIs

#### 1. Campaign Statistics
```python
# GET /api/method/trackflow.api.campaign.get_campaign_stats
params = {"campaign_name": "Q4 Email Marketing"}

# Response
{
    "status": "success", 
    "data": {
        "total_clicks": 1250,
        "unique_visitors": 890,
        "conversions": 45,
        "conversion_rate": 5.06,
        "revenue": 12500.00,
        "roi_percentage": 150.0
    }
}
```

#### 2. Link Analytics
```python
# GET /api/method/trackflow.api.links.get_link_analytics
params = {"link_name": "LINK-2024-001"}

# Response  
{
    "status": "success",
    "data": {
        "short_code": "abc123",
        "destination_url": "https://example.com/demo",
        "clicks_today": 25,
        "clicks_total": 340,
        "unique_clicks": 285,
        "top_referrers": [...],
        "geographic_data": [...],
        "device_breakdown": {...}
    }
}
```

### CRM Integration APIs

#### 1. Lead Attribution Data
```python
# GET /api/method/trackflow.integrations.crm_lead.get_lead_tracking_data
params = {"lead": "LEAD-2024-001"}

# Response
{
    "status": "success",
    "data": {
        "visitor_id": "v_abc123456789",
        "source": "google",
        "medium": "organic",
        "campaign": "brand_search",
        "first_touch_date": "2024-01-01 09:15:00",
        "last_touch_date": "2024-01-01 11:30:00",
        "touch_count": 3,
        "session_history": [...],
        "click_history": [...],
        "conversions": [...]
    }
}
```

---

## Advanced Configuration

### 1. GDPR Compliance Setup

#### Enable Cookie Consent
```python
# Via TrackFlow Settings
settings = frappe.get_single("TrackFlow Settings")
settings.gdpr_compliance_enabled = 1
settings.cookie_consent_required = 1
settings.cookie_consent_text = "We use cookies to track your marketing interactions..."
settings.privacy_policy_link = "https://yoursite.com/privacy"
settings.cookie_policy_link = "https://yoursite.com/cookies"
settings.save()
```

#### Cookie Consent JavaScript
```javascript
// Check consent before tracking
if (trackflow.hasConsent()) {
    trackflow.track('page_view');
} else {
    trackflow.showConsentBanner();
}

// Handle consent
trackflow.giveConsent().then(() => {
    trackflow.track('page_view');
    trackflow.track('consent_given');
});
```

### 2. Internal Traffic Filtering

#### Configure IP Ranges
```python
# Add internal IP ranges
settings = frappe.get_single("TrackFlow Settings")
settings.exclude_internal_traffic = 1

# Add IP ranges (supports CIDR notation)
settings.append("internal_ip_ranges", {
    "ip_range": "192.168.1.0/24",
    "description": "Office Network"
})
settings.append("internal_ip_ranges", {
    "ip_range": "10.0.0.0/8", 
    "description": "VPN Network"
})
settings.save()
```

### 3. Custom Domain Configuration

#### Set up Custom Short Domain
```python
# Configure custom domain for short links
settings = frappe.get_single("TrackFlow Settings")
settings.default_shortlink_domain = "track.yourcompany.com"
settings.save()

# DNS Configuration Required:
# track.yourcompany.com CNAME -> your-frappe-site.com
```

#### SSL & Security Headers
```nginx
# Nginx configuration for custom domain
server {
    server_name track.yourcompany.com;
    
    location /r/ {
        proxy_pass https://your-frappe-site.com;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # SSL configuration
    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/private.key;
}
```

### 4. Performance Optimization

#### Database Indexes
```sql
-- Add custom indexes for high-traffic queries
CREATE INDEX idx_custom_campaign_date ON `tabClick Event` (campaign, DATE(click_timestamp));
CREATE INDEX idx_custom_visitor_source ON `tabVisitor` (source, medium, creation);
CREATE INDEX idx_custom_conversion_value ON `tabConversion` (conversion_date, conversion_value);
```

#### Caching Strategy
```python
# Configure Redis caching
# In site_config.json
{
    "redis_cache": "redis://localhost:6379/1",
    "redis_queue": "redis://localhost:6379/2",
    "redis_socketio": "redis://localhost:6379/3"
}

# Enable caching for frequent queries
@frappe.whitelist()
@frappe.cache.memoize(timeout=300)  # 5 minutes
def get_campaign_stats(campaign_name):
    return frappe.call("trackflow.api.campaign.get_campaign_stats", campaign_name=campaign_name)
```

#### Background Job Processing
```python
# Process high-volume events in background
@frappe.whitelist(allow_guest=True)
def track_event_async():
    # Queue event for background processing
    frappe.enqueue('trackflow.tasks.process_click_event', 
                   event_data=frappe.local.form_dict,
                   queue='long')
    
    return {"status": "queued"}
```

---

## Troubleshooting

### Common Issues

#### 1. TrackFlow Not Visible in CRM
```python
# Run CRM integration setup
frappe.call("trackflow.install.setup_crm_integration")

# Clear cache
frappe.clear_cache()

# Check workspace
workspace = frappe.get_doc("Workspace", "CRM")
print([link.label for link in workspace.links if 'trackflow' in link.label.lower()])
```

#### 2. Tracking Script Not Loading
```python
# Check settings
settings = frappe.get_single("TrackFlow Settings")
print(f"Tracking enabled: {settings.enable_tracking}")

# Check website settings
website = frappe.get_single("Website Settings")
print("TrackFlow" in (website.head_html or ""))

# Manually add script
if "TrackFlow" not in (website.head_html or ""):
    website.head_html = (website.head_html or "") + """
    <!-- TrackFlow Analytics -->
    <script src="/api/method/trackflow.api.tracking.get_tracking_script" async></script>
    <!-- End TrackFlow Analytics -->
    """
    website.save()
```

#### 3. Attribution Not Working
```python
# Check custom fields
lead = frappe.get_doc("CRM Lead", "LEAD-001")
print(f"Visitor ID: {getattr(lead, 'trackflow_visitor_id', 'Not found')}")

# Check document hooks
print(frappe.get_hooks("doc_events").get("CRM Lead", {}))

# Test hook manually
frappe.call("trackflow.integrations.crm_lead.on_lead_create", lead, "after_insert")
```

#### 4. Performance Issues
```python
# Check database indexes
frappe.db.sql("SHOW INDEX FROM `tabClick Event`")

# Monitor query performance  
frappe.db.sql("SELECT * FROM information_schema.PROCESSLIST WHERE TIME > 5")

# Enable slow query logging
frappe.db.sql("SET GLOBAL slow_query_log = 'ON'")
frappe.db.sql("SET GLOBAL long_query_time = 2")
```

### Debug Mode

#### Enable Debug Logging
```python
# In site_config.json
{
    "developer_mode": 1,
    "logging": 2,
    "trackflow_debug": 1
}

# Check error logs
frappe.get_all("Error Log", 
               filters={"error": ["like", "%TrackFlow%"]}, 
               order_by="creation desc")
```

#### Test APIs Directly
```python
# Test tracking in console
frappe.call("trackflow.api.tracking.track_event", 
           event_type="test_event",
           visitor_id="v_test123",
           page_url="/test")

# Test CRM integration
test_lead = frappe.get_doc("CRM Lead", "LEAD-001")
frappe.call("trackflow.integrations.crm_lead.on_lead_create", test_lead, None)
```

---

## Migration Guide

### From Version 1.0 to 2.0

#### Database Schema Updates
```bash
# Run migration patches
bench migrate --site your-site.com

# Verify schema
frappe-bench$ frappe --site your-site.com execute trackflow.install.verify_schema
```

#### Configuration Changes
```python
# Update deprecated settings
old_settings = {
    "enable_bot_detection": "filter_bot_traffic",
    "click_notification_threshold": "alert_threshold_clicks",
    "notification_recipients": "admin_email_list"
}

settings = frappe.get_single("TrackFlow Settings") 
for old_field, new_field in old_settings.items():
    if hasattr(settings, old_field) and not hasattr(settings, new_field):
        setattr(settings, new_field, getattr(settings, old_field))
settings.save()
```

### Backup & Restore

#### Backup TrackFlow Data
```bash
# Export all TrackFlow doctypes
frappe --site your-site.com export-fixtures \
  --with-file-data \
  --doctype "Link Campaign" \
  --doctype "Tracked Link" \
  --doctype "Click Event" \
  --doctype "Visitor" \
  --doctype "Visitor Session"

# Create database dump
mysqldump -u root -p your_site_db > trackflow_backup.sql
```

#### Restore Process
```bash
# Restore database
mysql -u root -p your_site_db < trackflow_backup.sql

# Import fixtures
frappe --site your-site.com import-doc trackflow_export.json

# Rebuild search index
frappe --site your-site.com rebuild-global-search
```

---

*Generated: $(date)*
*Implementation Guide Version: 2.0*
*TrackFlow Status: Production Ready*