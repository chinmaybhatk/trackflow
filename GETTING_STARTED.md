# 🚀 TrackFlow Getting Started Guide

Complete step-by-step guide to start using TrackFlow for marketing attribution and link tracking.

## 📋 Prerequisites

1. ✅ Frappe Cloud site with TrackFlow installed
2. ✅ Frappe CRM app installed
3. ✅ Administrator access to the site
4. ✅ Migration completed successfully

---

## 🎯 Step 1: Access TrackFlow

### Method 1: Via CRM Sidebar
1. Go to your Frappe Cloud site: `https://[your-site].frappe.cloud`
2. Login with Administrator credentials
3. Navigate to **CRM** workspace
4. Look for **"TrackFlow Analytics"** section in the sidebar
5. You should see:
   - 📊 **Campaigns**
   - 🔗 **Tracked Links** 
   - 📈 **Click Analytics**

### Method 2: Via TrackFlow Workspace
1. From the main dashboard, click on **"TrackFlow"** in the workspace list
2. Access all TrackFlow features from the dedicated workspace

---

## ⚙️ Step 2: Configure TrackFlow Settings

1. Go to **TrackFlow** workspace → **Settings**
2. Or navigate to: `[your-site]/app/trackflow-settings`
3. Configure basic settings:

```
✅ Basic Configuration:
Enable Tracking: ✓ Checked
Auto Generate Short Codes: ✓ Checked  
Short Code Length: 6
Default Shortlink Domain: [leave empty to use your site domain]

✅ Attribution Settings:
Default Attribution Model: Last Touch
Attribution Window (days): 30

✅ Privacy Settings:
GDPR Compliance: ✓ Checked
Cookie Consent Required: ✓ Checked
Cookie Expires (days): 365
Exclude Internal Traffic: ✓ Checked
```

4. **Save** the settings

---

## 📊 Step 3: Create Your First Campaign

1. Go to **CRM** → **TrackFlow Analytics** → **Campaigns**
2. Click **"+ New"** button
3. Fill in the campaign details:

```
📝 SAMPLE CAMPAIGN DATA:

Campaign Name: Q4 Email Newsletter
Description: Holiday season email marketing campaign targeting existing customers
Campaign Type: Email Marketing
Status: Active
Start Date: [Today's date]
End Date: [30 days from today]

UTM Parameters:
Source: newsletter
Medium: email  
Campaign: q4-holiday
Term: [leave empty]
Content: main-cta

Budget Information:
Budget: 5000
Currency: USD
Budget Period: Monthly

Goals:
Primary Goal: Lead Generation
Target Clicks: 1000
Target Conversions: 50
Target Revenue: 25000
```

4. **Save** the campaign

---

## 🔗 Step 4: Create Tracked Links

1. Go to **CRM** → **TrackFlow Analytics** → **Tracked Links**
2. Click **"+ New"** button
3. Create multiple sample links:

### Link 1: Product Page
```
📝 SAMPLE LINK DATA:

Link Name: Holiday Products Landing Page
Campaign: Q4 Email Newsletter [select from dropdown]
Target URL: https://yourstore.com/holiday-products
Description: Main product showcase for holiday campaign

Short URL Settings:
Auto Generate Short Code: ✓ Checked
Custom Short Code: [leave empty - will auto generate]
Status: Active

Tracking Options:
Track Clicks: ✓ Checked
Generate QR Code: ✓ Checked
Enable UTM Parameters: ✓ Checked
```

### Link 2: Special Offer
```
Link Name: 20% Off Holiday Special
Campaign: Q4 Email Newsletter
Target URL: https://yourstore.com/holiday-special?discount=20OFF
Description: Special discount link for email subscribers

[Same tracking settings as above]
```

### Link 3: Blog Content
```
Link Name: Holiday Gift Guide Blog
Campaign: Q4 Email Newsletter  
Target URL: https://yourstore.com/blog/holiday-gift-guide
Description: Educational content to drive engagement

[Same tracking settings as above]
```

4. **Save** each link
5. **Copy the generated short URLs** - you'll use these in your marketing

---

## 🎯 Step 5: Test Link Tracking

1. **Get your short URLs** from the Tracked Links list
2. **Open each short URL** in a new browser tab/incognito window
3. You should be redirected to the target URLs
4. **Verify tracking is working**:
   - Go to **Click Analytics** 
   - You should see click events for each link you tested
   - Check visitor information, browser details, timestamps

---

## 📈 Step 6: View Analytics & Data

### Check Click Events
1. Go to **CRM** → **TrackFlow Analytics** → **Click Analytics**
2. You should see entries for your test clicks with:
   - Visitor ID
   - Tracked Link
   - Click timestamp
   - Browser/device information
   - Campaign attribution

### Check Visitors
1. Go to **TrackFlow** workspace → **Visitors**
2. View visitor sessions and journey data

### Campaign Performance
1. Return to your **Campaign** (Q4 Email Newsletter)
2. Check the statistics:
   - Total clicks
   - Unique visitors
   - Click-through rates

---

## 🎭 Step 7: Simulate Lead Generation

1. **Create a test CRM Lead**:
   - Go to **CRM** → **Leads** → **+ New**
   - Fill in basic information:

```
📝 SAMPLE LEAD DATA:

Lead Name: John Test Customer
Email: john.test@example.com
Mobile: +1-555-0123
Organization: Test Company
Status: Open

🔑 IMPORTANT: In the TrackFlow tab, add:
TrackFlow Visitor ID: [copy from a visitor record in Click Analytics]
Source: newsletter
Medium: email
Campaign: Q4 Email Newsletter
```

2. **Save the lead**
3. **Check attribution**: The lead should now be attributed to your campaign

---

## 🏆 Step 8: Test Deal Attribution

1. **Convert Lead to Deal**:
   - Open your test lead
   - Click **"Create Deal"** or manually create a deal
   - Link it to the test lead

2. **Check Deal Attribution**:
   - Open the deal
   - Go to **TrackFlow Attribution** tab
   - Verify attribution data inherited from the lead

---

## 📊 Step 9: Review Complete Analytics

### Campaign ROI Analysis
1. Review your **Q4 Email Newsletter** campaign
2. Check metrics:
   - Total clicks: [your test clicks]
   - Conversions: [leads/deals created]
   - Conversion rate
   - Attribution data

### Visitor Journey
1. Go to **Visitors** list
2. Open a visitor record
3. Review their complete journey:
   - Click events
   - Session data
   - Attribution details
   - Linked leads/deals

---

## 🔧 Step 10: Advanced Configuration

### Attribution Models
1. Go to **TrackFlow** workspace → **Attribution Models**
2. Create custom attribution rules
3. Test different attribution approaches

### Custom UTM Parameters
1. Create campaigns with different UTM combinations
2. Test tracking across multiple channels:
   - Social media campaigns
   - Google Ads campaigns  
   - Direct email campaigns
   - Partner/affiliate campaigns

---

## 🎯 Real-World Usage Scenarios

### Email Marketing Campaign
```
1. Create campaign: "Weekly Newsletter #47"
2. Create links for each email section:
   - Header CTA → Product page
   - Main content → Blog post
   - Footer offer → Discount page
3. Send email with tracked links
4. Monitor click performance
5. Track leads generated from email
```

### Social Media Campaign
```
1. Create campaign: "Instagram Holiday Promo"
2. Create tracked links for:
   - Instagram bio link
   - Story swipe-up links
   - Post CTAs
3. Post content with tracked links
4. Monitor social traffic and conversions
```

### Multi-Channel Attribution
```
1. Create separate campaigns for each channel
2. Use consistent UTM parameters
3. Track customer journey across touchpoints
4. Analyze which channels drive highest value
```

---

## ✅ Success Checklist

After completing this guide, you should have:

- ✅ **Configured TrackFlow Settings** with your preferences
- ✅ **Created sample campaigns** with proper UTM parameters  
- ✅ **Generated tracked links** that redirect correctly
- ✅ **Verified click tracking** is working
- ✅ **Created attributed leads** linked to campaigns
- ✅ **Tested deal attribution** inheritance
- ✅ **Reviewed analytics** showing complete visitor journeys
- ✅ **Understanding of ROI tracking** for campaigns

---

## 🚨 Troubleshooting

### Links Not Redirecting
- Check Target URL is valid and accessible
- Verify TrackFlow Settings has "Enable Tracking" checked
- Check link status is "Active"

### No Click Events Showing
- Verify you're not on internal IP (check Internal IP Ranges in settings)
- Clear browser cache and try again
- Check if JavaScript is enabled

### Attribution Not Working
- Ensure Visitor ID is correctly set on leads
- Check Attribution Window hasn't expired
- Verify UTM parameters match between links and campaigns

### Settings Page Error
- Run migration: `bench --site [site] migrate`
- Check Internal IP Range DocType exists
- Verify TrackFlow Settings document exists

---

## 🎉 Next Steps

1. **Test with real campaigns** using actual URLs
2. **Train your marketing team** on creating tracked links
3. **Set up regular reporting** on campaign performance  
4. **Integrate with your website** for automatic tracking
5. **Explore advanced attribution models** for complex customer journeys

You're now ready to use TrackFlow for comprehensive marketing attribution! 🚀