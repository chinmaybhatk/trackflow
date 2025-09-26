# ⚡ TrackFlow Quick Start

**5-minute setup to start tracking your marketing campaigns**

## 🚀 Essential Steps

### 1. Configure Settings
```
Go to: TrackFlow workspace → Settings
✅ Enable Tracking: ON
✅ Auto Generate Short Codes: ON  
✅ Attribution Model: Last Touch
✅ GDPR Compliance: ON
```

### 2. Create Sample Campaign
```
Go to: CRM → Campaigns → + New

Campaign Name: Test Email Campaign
Source: newsletter
Medium: email
Campaign: test-campaign
Status: Active
```

### 3. Create Tracked Link
```
Go to: CRM → Tracked Links → + New

Link Name: Test Product Link
Campaign: [Select your campaign]
Target URL: https://example.com/products
✅ Auto Generate Short Code: ON
✅ Track Clicks: ON
```

### 4. Test & Verify
```
1. Copy the generated short URL
2. Open in new browser tab
3. Check: CRM → Click Analytics
4. Verify click event recorded
```

### 5. Create Attributed Lead
```
Go to: CRM → Leads → + New

Name: Test Customer
Email: test@example.com
TrackFlow Tab:
  - Visitor ID: [copy from click event]
  - Source: newsletter
  - Campaign: Test Email Campaign
```

## ✅ Success Check
- ✅ Short link redirects correctly
- ✅ Click events appear in analytics
- ✅ Lead shows attribution data
- ✅ Campaign shows click statistics

**🎉 You're ready to track real campaigns!**