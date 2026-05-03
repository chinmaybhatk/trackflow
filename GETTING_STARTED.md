# 🚀 TrackFlow Getting Started Guide

**Complete installation and setup guide for TrackFlow marketing attribution platform**

## Prerequisites

- **Frappe Framework v16+** with Python 3.14+
- **Node.js 24+** for asset builds
- **Frappe CRM** installed and configured
- **MariaDB/MySQL** database backend
- **Administrator access** to your Frappe site

## Installation

### Method 1: One-Command Install
```bash
# Navigate to your bench directory
cd ~/frappe-bench

# Get TrackFlow from GitHub
bench get-app https://github.com/chinmaybhatk/trackflow.git

# Install on your site
bench --site your-site-name install-app trackflow

# Apply workspace fixture and build assets
bench --site your-site-name migrate
bench build --app trackflow
```

### Method 2: Manual Installation
```bash
# Clone and install
cd frappe-bench/apps
git clone https://github.com/chinmaybhatk/trackflow.git
bench install-app trackflow --site your-site-name

# Run migrations, build, restart
bench --site your-site-name migrate
bench build --app trackflow
bench restart
```

### Verify Installation
```bash
# Check installation
bench --site your-site-name console
>>> import trackflow
>>> frappe.get_installed_apps()  # Should include 'trackflow'
```

## Initial Configuration

### 1. Access TrackFlow
TrackFlow is registered as its own app in the Frappe v16 desk.

- Open `https://[your-site]/desk/trackflow`
- The desk shows a **"T TrackFlow"** badge in the top-left and a sidebar with **Home**, **Dashboard**, **Campaigns**, and **Tracked Links**
- Shortcut cards on the home page jump straight to Dashboard, Campaigns, Tracked Links, and Settings

> Note: Frappe CRM is a separate SPA at `/crm/`, so TrackFlow does not appear inside the CRM frontend itself — use the Frappe desk URL above for the TrackFlow workspace.

### 2. Configure Settings
1. Open the **Settings** shortcut from the TrackFlow workspace, or
2. Navigate to: `[your-site]/app/trackflow-settings`

**Basic Configuration:**
```
✅ Enable Tracking: ON
✅ Auto Generate Short Codes: ON  
✅ Short Code Length: 6
✅ Attribution Model: Last Touch
✅ Attribution Window: 30 days
✅ GDPR Compliance: ON (recommended)
✅ Cookie Consent Required: ON (recommended)
✅ Exclude Internal Traffic: ON
```

## Quick Setup Workflow

### Step 1: Create Your First Campaign
```
Go to: TrackFlow workspace → Campaigns → + New

Campaign Name: Test Email Campaign
Description: Holiday season email marketing
Campaign Type: Email Marketing
Status: Active
Start Date: [Today's date]
End Date: [30 days from today]

UTM Parameters:
Source: newsletter
Medium: email  
Campaign: test-campaign
Budget: 5000 USD
```

### Step 2: Generate Tracked Links
```
Go to: TrackFlow workspace → Tracked Links → + New

Link Name: Test Product Link
Campaign: [Select your campaign]
Target URL: https://example.com/products
✅ Auto Generate Short Code: ON
✅ Track Clicks: ON
✅ Generate QR Code: ON
```

### Step 3: Test Link Tracking
1. **Copy the generated short URL** from the Tracked Links list
2. **Open in a new browser tab/incognito window**
3. **Verify tracking works**:
   - Go to **Click Analytics** 
   - Check for click events with browser details and timestamps

### Step 4: Create Attributed Lead
```
Go to: CRM → Leads → + New

Lead Name: Test Customer
Email: test@example.com
TrackFlow Tab:
  - Visitor ID: [copy from click event]
  - Source: newsletter
  - Medium: email
  - Campaign: Test Email Campaign
```

### Step 5: Verify Attribution
1. **Check Click Events**: TrackFlow workspace → Click Analytics
2. **Check Visitors**: TrackFlow workspace → Visitors  
3. **Campaign Performance**: Return to your campaign to see statistics

## Advanced Setup

### External Website Tracking
For tracking visitors on external websites (WordPress, Shopify, custom sites):

**1. Configure Cross-Domain Settings**
```python
# In TrackFlow Settings
settings.enable_cross_domain_tracking = 1
settings.append("allowed_domains", {
    "domain": "yourcompany.com",
    "description": "Main marketing website"
})
```

**2. Embed Tracking Script**
```html
<!-- Add to external website <head> -->
<script>
(function(t,r,a,c,k,f,l,o,w) {
    t['TrackFlowObject'] = k;
    t[k] = t[k] || function() { (t[k].q = t[k].q || []).push(arguments) };
    f = r.createElement(a), l = r.getElementsByTagName(a)[0];
    f.async = 1; f.src = c; l.parentNode.insertBefore(f, l);
})(window, document, 'script', 'https://your-site.com/api/method/trackflow.api.tracking.get_tracking_script', 'trackflow');

trackflow('config', {
    server_url: 'https://your-site.com',
    site_domain: 'yourcompany.com'
});
trackflow('page_view');
</script>
```

**3. Track Form Submissions**
```javascript
// Auto-populate tracking fields in forms
document.addEventListener('DOMContentLoaded', function() {
    const visitorData = trackflow('get_visitor_data');
    document.getElementById('tf-visitor').value = visitorData.visitor_id;
    document.getElementById('tf-source').value = visitorData.source;
    document.getElementById('tf-campaign').value = visitorData.campaign;
});
```

### Attribution Models
TrackFlow supports 5 attribution models:

1. **Last Touch** (Default) - 100% credit to final interaction
2. **First Touch** - 100% credit to initial touchpoint  
3. **Linear** - Equal credit across all touchpoints
4. **Time Decay** - Recent interactions weighted higher
5. **Position Based** - 40% first, 40% last, 20% middle

Configure in **TrackFlow** → **Attribution Models**

## Development Setup

### Local Docker Development
```bash
git clone https://github.com/chinmaybhatk/trackflow.git
cd trackflow
./dev.sh start

# Access at http://localhost:8000
# Username: Administrator
# Password: admin
```

### Local Bench Development
```bash
# Install in development mode
bench get-app . --skip-assets
bench --site your-site.local install-app trackflow
bench --site your-site.local set-config developer_mode 1
```

## Troubleshooting

### Common Issues

**TrackFlow Not Visible in CRM**
```bash
# Clear cache and restart
bench clear-cache --site your-site
bench restart

# Check workspace integration
frappe.call("trackflow.install.setup_crm_integration")
```

**Links Not Redirecting**
- Verify Target URL is accessible
- Check TrackFlow Settings has "Enable Tracking" enabled
- Ensure link status is "Active"

**No Click Events Showing**
- Check if you're on internal IP (excluded by default)
- Clear browser cache and try again
- Verify JavaScript is enabled

**Attribution Not Working**
- Ensure Visitor ID is correctly set on leads
- Check Attribution Window hasn't expired (default 30 days)
- Verify UTM parameters match between links and campaigns

### Debug Commands
```python
# Check installation
bench --site your-site console
>>> import trackflow
>>> frappe.get_single("TrackFlow Settings")

# Test attribution
lead = frappe.get_doc("CRM Lead", "LEAD-001")
print(f"Attribution: {lead.trackflow_source} / {lead.trackflow_campaign}")

# Check API endpoints
frappe.call("trackflow.api.tracking.track_event", 
           event_type="test", visitor_id="test123")
```

## Success Checklist

After completing this guide, you should have:

- ✅ **TrackFlow installed** and accessible in CRM
- ✅ **Settings configured** with your preferences  
- ✅ **Test campaign created** with proper UTM parameters
- ✅ **Tracked links generated** that redirect correctly
- ✅ **Click tracking verified** with analytics showing
- ✅ **Attributed leads created** linked to campaigns
- ✅ **Attribution working** with complete visitor journeys

## Next Steps

1. **Create real campaigns** with actual marketing URLs
2. **Train your team** on creating tracked links
3. **Set up regular reporting** on campaign performance  
4. **Integrate with external websites** for comprehensive tracking
5. **Explore advanced attribution models** for complex customer journeys

For detailed implementation guides, see [docs/IMPLEMENTATION.md](docs/IMPLEMENTATION.md)

---

**🎉 You're ready to track comprehensive marketing attribution with TrackFlow!**