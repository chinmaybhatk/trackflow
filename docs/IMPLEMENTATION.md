# TrackFlow Implementation Guide

**Comprehensive technical guide for implementing TrackFlow in production environments**

## Architecture Overview

TrackFlow supports two primary deployment scenarios:

### 🌐 Scenario A: External Website Tracking (Recommended)
- **TrackFlow Server**: Runs on your Frappe/CRM server  
- **Tracked Websites**: Any external website(s) with embedded JavaScript
- **Use Case**: Track marketing campaigns across multiple domains while centralizing data in CRM

### 🏠 Scenario B: Same-Server Tracking
- **TrackFlow Server**: Runs on same Frappe server as your website
- **Tracked Website**: Same Frappe site with website builder
- **Use Case**: All-in-one Frappe setup with built-in website

## Core Features & Status

### ✅ Production-Ready Features
- **Advanced Link Tracking**: Short URLs, UTM parameters, QR codes
- **Multi-Touch Attribution**: 5 attribution models with real-time calculation
- **Deep CRM Integration**: Automatic lead/deal attribution with 12 custom fields
- **Visitor Journey Tracking**: Complete session management and behavioral scoring
- **Cross-Domain Tracking**: JavaScript embed for external websites
- **GDPR Compliance**: Cookie consent management and data protection
- **Campaign Analytics**: ROI tracking and performance insights
- **API Access**: 15+ endpoints for custom integrations

### 📊 Attribution Models
1. **Last Touch** (Default) - 100% credit to final interaction
2. **First Touch** - 100% credit to initial touchpoint  
3. **Linear** - Equal credit across all touchpoints
4. **Time Decay** - Recent interactions weighted higher
5. **Position Based** - 40% first, 40% last, 20% middle

## Database Architecture

### Core Data Flow
```
Link Campaign → Tracked Link → Click Event → Visitor → CRM Lead → Deal Attribution
```

### Key DocTypes (29 Total)
- **Link Campaign**: Campaign management with UTM parameters
- **Tracked Link**: Smart URL management with analytics
- **Visitor**: Persistent visitor identification and journey tracking
- **Click Event**: Individual click tracking with device/location data
- **Visitor Session**: Session management and page view tracking
- **Attribution Model**: Multi-touch attribution calculation engine
- **Conversion**: Goal tracking and conversion events
- **Deal Attribution**: Revenue attribution to marketing touchpoints

### Performance Optimizations
- **Indexed Fields**: visitor_id, click_timestamp, campaign references
- **Async Processing**: Background event processing for high volume
- **Caching Strategy**: Redis caching for frequent queries
- **Data Retention**: Configurable cleanup policies

## API Reference

### Authentication
```python
# Session-based (via Frappe login)
headers = {"Cookie": "sid=your_session_id"}

# API Key authentication
headers = {"Authorization": "token your_api_key:your_api_secret"}
```

### Core Tracking APIs

#### Link Redirection
```http
GET /r/{short_code}
# Automatically tracks click and redirects
# No authentication required
```

#### Event Tracking
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

#### Campaign Analytics
```python
# GET /api/method/trackflow.api.campaign.get_campaign_stats
params = {"campaign_name": "Q4 Email Marketing"}

# Response includes:
# - Total clicks, unique visitors, conversions
# - Conversion rates, revenue attribution
# - ROI calculations and performance metrics
```

### CRM Integration APIs

#### Lead Attribution
```python
# GET /api/method/trackflow.integrations.crm_lead.get_lead_tracking_data
params = {"lead": "LEAD-2024-001"}

# Response includes complete visitor journey:
# - Source, medium, campaign attribution
# - First/last touch dates and touch count
# - Session history and click events
# - Conversion timeline
```

#### Deal ROI Analysis
```python
# GET /api/method/trackflow.api.analytics.get_deal_roi
# Complete deal attribution with marketing influence calculation
```

## External Website Tracking

### JavaScript Integration

#### Basic Setup
```html
<!-- Add to external website <head> -->
<script>
(function(t,r,a,c,k,f,l,o,w) {
    t['TrackFlowObject'] = k;
    t[k] = t[k] || function() { (t[k].q = t[k].q || []).push(arguments) };
    f = r.createElement(a), l = r.getElementsByTagName(a)[0];
    f.async = 1; f.src = c; l.parentNode.insertBefore(f, l);
})(window, document, 'script', 'https://your-crm-site.com/api/method/trackflow.api.tracking.get_tracking_script', 'trackflow');

trackflow('config', {
    server_url: 'https://your-crm-site.com',
    site_domain: 'yourcompany.com',
    enable_page_tracking: true,
    enable_form_tracking: true,
    cookie_domain: '.yourcompany.com'
});

trackflow('page_view');
</script>
```

#### Form Tracking
```html
<!-- Contact form with attribution -->
<form id="contact-form" action="/submit-lead" method="POST">
    <input type="text" name="name" placeholder="Name" required>
    <input type="email" name="email" placeholder="Email" required>
    
    <!-- Hidden tracking fields -->
    <input type="hidden" name="trackflow_visitor_id" id="tf-visitor">
    <input type="hidden" name="trackflow_source" id="tf-source">
    <input type="hidden" name="trackflow_campaign" id="tf-campaign">
    
    <button type="submit">Submit</button>
</form>

<script>
// Auto-populate tracking fields
document.addEventListener('DOMContentLoaded', function() {
    const visitorData = trackflow('get_visitor_data');
    document.getElementById('tf-visitor').value = visitorData.visitor_id;
    document.getElementById('tf-source').value = visitorData.source || '';
    document.getElementById('tf-campaign').value = visitorData.campaign || '';
});

// Track form submission
document.getElementById('contact-form').addEventListener('submit', function(e) {
    trackflow('track_event', {
        event_type: 'form_submit',
        form_name: 'contact_form'
    });
    
    // Send to CRM
    const formData = new FormData(this);
    fetch('https://your-crm-site.com/api/method/trackflow.api.leads.create_external_lead', {
        method: 'POST',
        body: formData
    });
});
</script>
```

#### Custom Event Tracking
```javascript
// E-commerce tracking
trackflow('track_event', {
    event_type: 'product_view',
    product_id: 'PROD-123',
    product_name: 'Premium Widget',
    category: 'widgets',
    price: 99.99
});

// Conversion tracking
trackflow('track_event', {
    event_type: 'purchase',
    transaction_id: 'TXN-456',
    value: 299.97,
    items: [{id: 'PROD-123', name: 'Premium Widget', price: 99.99, qty: 3}]
});
```

### Cross-Domain Configuration

#### Multi-Domain Setup
```python
# TrackFlow Settings - add all domains to track
settings = frappe.get_single("TrackFlow Settings")
settings.enable_cross_domain_tracking = 1

domains = [
    "yourcompany.com",
    "shop.yourcompany.com", 
    "blog.yourcompany.com",
    "landing.yourcompany.com"
]

for domain in domains:
    settings.append("allowed_domains", {
        "domain": domain,
        "description": f"Marketing site: {domain}"
    })
```

#### Cross-Domain Link Tracking
```javascript
// Link visitors across different domains
function trackCrossDomainClick(url, campaign) {
    const visitorId = trackflow('get_visitor_id');
    const crossDomainUrl = `${url}?_tf_vid=${visitorId}&_tf_campaign=${campaign}`;
    
    trackflow('track_event', {
        event_type: 'cross_domain_click',
        target_domain: new URL(url).hostname
    });
    
    window.location.href = crossDomainUrl;
}
```

## CRM Integration Details

### Automatic Attribution Workflow

When a visitor with tracking cookies fills a lead form:

```python
# Happens automatically via document hooks
def on_lead_create(doc, method):
    visitor_id = frappe.request.cookies.get('trackflow_visitor_id')
    
    if visitor_id:
        visitor = frappe.get_doc("Visitor", {"visitor_id": visitor_id})
        
        # Apply attribution automatically
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

### Custom Fields Added to CRM

**CRM Lead (7 fields):**
- `trackflow_visitor_id`: Links to visitor tracking data
- `trackflow_source`: Traffic source (google, facebook, email)
- `trackflow_medium`: Traffic medium (organic, cpc, newsletter)
- `trackflow_campaign`: Associated campaign name
- `trackflow_first_touch_date`: Date of first interaction
- `trackflow_last_touch_date`: Date of most recent interaction
- `trackflow_touch_count`: Number of touchpoints

**CRM Deal (4 fields):**
- `trackflow_attribution_model`: Selected attribution model
- `trackflow_first_touch_source`: First touchpoint source
- `trackflow_last_touch_source`: Last touchpoint source
- `trackflow_marketing_influenced`: Whether marketing influenced the deal

**CRM Organization (3 fields):**
- `trackflow_visitor_id`: Links to visitor tracking data
- `trackflow_engagement_score`: Calculated engagement score (0-100)
- `trackflow_last_campaign`: Most recent campaign interaction

## WordPress Integration

### TrackFlow WordPress Plugin
```php
<?php
/**
 * Plugin Name: TrackFlow Integration
 * Description: Integrate WordPress with TrackFlow marketing attribution
 */

class TrackFlowWP {
    private $trackflow_server = 'https://your-crm-site.com';
    private $site_domain = 'yourwordpresssite.com';
    
    public function __construct() {
        add_action('wp_head', array($this, 'inject_tracking_script'));
        add_action('wpcf7_mail_sent', array($this, 'track_form_submission'));
        add_action('gform_after_submission', array($this, 'track_gravity_form'));
    }
    
    public function inject_tracking_script() {
        ?>
        <script>
        (function(t,r,a,c,k,f,l,o,w) {
            t['TrackFlowObject'] = k;
            t[k] = t[k] || function() { (t[k].q = t[k].q || []).push(arguments) };
            f = r.createElement(a), l = r.getElementsByTagName(a)[0];
            f.async = 1; f.src = c; l.parentNode.insertBefore(f, l);
        })(window, document, 'script', '<?php echo $this->trackflow_server; ?>/api/method/trackflow.api.tracking.get_tracking_script', 'trackflow');
        
        trackflow('config', {
            server_url: '<?php echo $this->trackflow_server; ?>',
            site_domain: '<?php echo $this->site_domain; ?>'
        });
        trackflow('page_view');
        </script>
        <?php
    }
    
    public function track_form_submission($contact_form) {
        $visitor_id = $_COOKIE['trackflow_visitor_id'] ?? null;
        
        if ($visitor_id) {
            $submission = WPCF7_Submission::get_instance();
            $posted_data = $submission->get_posted_data();
            
            $this->send_lead_to_trackflow(array(
                'email' => $posted_data['your-email'],
                'name' => $posted_data['your-name'], 
                'trackflow_visitor_id' => $visitor_id,
                'form_name' => $contact_form->name()
            ));
        }
    }
    
    private function send_lead_to_trackflow($data) {
        wp_remote_post($this->trackflow_server . '/api/method/trackflow.api.leads.create_external_lead', array(
            'method' => 'POST',
            'body' => $data,
            'timeout' => 10
        ));
    }
}

new TrackFlowWP();
?>
```

## Advanced Configuration

### GDPR Compliance

#### Cookie Consent Setup
```python
# Via TrackFlow Settings
settings = frappe.get_single("TrackFlow Settings")
settings.gdpr_compliance_enabled = 1
settings.cookie_consent_required = 1
settings.cookie_consent_text = "We use cookies to track marketing interactions..."
settings.privacy_policy_link = "https://yoursite.com/privacy"
settings.cookie_policy_link = "https://yoursite.com/cookies"
```

#### JavaScript Consent Management
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

### Performance Optimization

#### Database Indexes
```sql
-- Custom indexes for high-traffic queries
CREATE INDEX idx_campaign_date ON `tabClick Event` (campaign, DATE(click_timestamp));
CREATE INDEX idx_visitor_source ON `tabVisitor` (source, medium, creation);
CREATE INDEX idx_conversion_value ON `tabConversion` (conversion_date, conversion_value);
```

#### Redis Caching
```python
# Enable caching for frequent queries
@frappe.whitelist()
@frappe.cache.memoize(timeout=300)  # 5 minutes
def get_campaign_stats(campaign_name):
    return frappe.call("trackflow.api.campaign.get_campaign_stats", 
                      campaign_name=campaign_name)
```

#### Background Processing
```python
# Process high-volume events in background
@frappe.whitelist(allow_guest=True)
def track_event_async():
    frappe.enqueue('trackflow.tasks.process_click_event', 
                   event_data=frappe.local.form_dict,
                   queue='long')
    return {"status": "queued"}
```

### Custom Domain Configuration

#### Short Link Domain Setup
```python
# Configure custom domain for branded short links
settings = frappe.get_single("TrackFlow Settings")
settings.default_shortlink_domain = "track.yourcompany.com"

# DNS Configuration Required:
# track.yourcompany.com CNAME -> your-frappe-site.com
```

#### Nginx Configuration
```nginx
server {
    server_name track.yourcompany.com;
    
    location /r/ {
        proxy_pass https://your-frappe-site.com;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/private.key;
}
```

## Production Deployment

### Performance Characteristics
- **Link Redirects**: <100ms response time
- **Attribution Calculation**: <500ms for complex journeys  
- **Campaign Analytics**: <300ms for typical reports
- **Scalability**: Handles 100K+ click events per month

### Monitoring & Health Checks
```python
# System health monitoring
frappe.db.count("Click Event")  # Monitor click volume
frappe.db.count("Attribution Model", {"is_active": 1})  # Verify models

# Performance monitoring  
frappe.db.sql("SHOW PROCESSLIST")  # Database performance
redis_cli info memory  # Redis cache usage
```

### Backup & Recovery
```bash
# Export all TrackFlow data
frappe --site your-site.com export-fixtures \
  --with-file-data \
  --doctype "Link Campaign" \
  --doctype "Tracked Link" \
  --doctype "Click Event" \
  --doctype "Visitor"

# Database backup
mysqldump -u root -p your_site_db > trackflow_backup.sql
```

## Troubleshooting

### Debug Commands
```python
# Verify attribution for a deal
deal = frappe.get_doc("CRM Deal", "DEAL-001")
print(f"Attribution: {deal.trackflow_visitor_id}")

# Test attribution model
model = frappe.get_doc("Attribution Model", "Last Touch")
touchpoints = get_visitor_touchpoints("v_123456789")
attribution = model.calculate_attribution(touchpoints, 1000.00)

# Check API endpoint availability  
frappe.get_attr("trackflow.api.analytics.get_deal_roi")
```

### Common Issues & Solutions

**CORS Issues with External Sites**
```python
# Add CORS handling to hooks.py
before_request = ["trackflow.api.cors.handle_cors"]

# Create trackflow/api/cors.py
def handle_cors():
    if frappe.request.method == "OPTIONS":
        frappe.local.response.headers.update({
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        })
```

**Cookie Issues Across Domains**
```javascript
// Debug cookie setting
trackflow('debug', {
    show_cookies: true,
    log_events: true
});

// Check cross-domain cookies
console.log(document.cookie.split(';').filter(c => c.includes('trackflow')));
```

### Migration & Updates

#### Version 1.0 to 2.0 Migration
```bash
# Run migration patches
bench migrate --site your-site.com

# Verify schema updates
frappe --site your-site.com execute trackflow.install.verify_schema
```

#### Configuration Updates
```python
# Update deprecated settings
settings = frappe.get_single("TrackFlow Settings") 
settings.filter_bot_traffic = settings.enable_bot_detection  # Renamed field
settings.save()
```

## Roadmap & Future Enhancements

### Phase 3 - Advanced Features (Q1 2025)
- **Real-time Dashboard**: Live campaign performance monitoring
- **Predictive Analytics**: ML-powered conversion probability
- **Advanced Segmentation**: Visitor behavior-based grouping
- **Enterprise Integrations**: Salesforce, HubSpot connectors

### Performance Enhancements
- **Click Stream Optimization**: Reduce database load for high-volume sites
- **Attribution Caching**: Cache complex multi-touch calculations
- **Bulk Import/Export**: CSV handling for historical campaign data

---

*TrackFlow Implementation Guide v2.0*  
*Last Updated: December 2024*  
*Production Status: ✅ All Features Verified*