# TrackFlow - Smart Link Tracking and Attribution for Frappe CRM

TrackFlow is a comprehensive marketing attribution and link tracking app designed specifically for **Frappe CRM (FCRM)**. It helps businesses track marketing campaigns, understand customer journeys, and attribute revenue to the right marketing channels.

## 🚀 Project Status

**Version**: 1.0.0  
**Status**: Beta - Core features working, some integrations pending  
**Last Updated**: September 2025

### ✅ What's Working
- Link tracking and redirects
- Campaign management
- Click event tracking
- Visitor session tracking
- Attribution models (5 types)
- CRM Lead, Deal, and Organization integration
- Web form tracking
- Bulk link generation
- API endpoints

### ⚠️ Known Issues & Limitations
- Email tracking not implemented
- CRM Contact integration missing
- Activity/Task tracking not available
- Multi-currency support pending
- Real-time dashboard under development

## 📋 Features

### Core Functionality

#### 🔗 Link Management
- **Tracked Links**: Short URLs with automatic tracking
- **QR Code Generation**: For offline campaigns
- **Bulk Generation**: Create multiple links at once
- **Custom Identifiers**: Branded short codes
- **UTM Parameters**: Automatic tracking

#### 📊 Campaign Management
- **Link Campaigns**: Organize and track marketing efforts
- **Goal Setting**: Define and track objectives
- **Budget Tracking**: Monitor spending vs. revenue
- **Performance Metrics**: Real-time analytics

#### 🎯 Attribution & Analytics
- **5 Attribution Models**:
  - Last Touch (100% to final interaction)
  - First Touch (100% to initial interaction)
  - Linear (Equal distribution)
  - Time Decay (Recent interactions weighted more)
  - Position Based (40% first, 40% last, 20% middle)
- **Visitor Sessions**: Track complete user journey
- **Conversion Tracking**: Monitor goal achievement
- **Deal Attribution**: Link revenue to campaigns

### 🔌 Frappe CRM Integration

#### Integrated Entities
- **CRM Lead**: Automatic source tracking, visitor ID linkage
- **CRM Deal**: Attribution calculation, marketing influence
- **CRM Organization**: Engagement scoring, campaign tracking
- **Web Forms**: Conversion tracking, goal linkage

#### Custom Fields Added
```
CRM Lead:
- trackflow_visitor_id
- trackflow_source
- trackflow_medium
- trackflow_campaign
- trackflow_first_touch_date
- trackflow_last_touch_date
- trackflow_touch_count

CRM Deal:
- trackflow_attribution_model
- trackflow_first_touch_source
- trackflow_last_touch_source
- trackflow_marketing_influenced

CRM Organization:
- trackflow_visitor_id
- trackflow_engagement_score
- trackflow_last_campaign
```

## 💻 Installation

### Prerequisites
- Frappe Framework v15+
- Frappe CRM installed and configured
- Python 3.10+

### Quick Install

```bash
# Navigate to bench directory
cd ~/frappe-bench

# Get the app
bench get-app https://github.com/chinmaybhatk/trackflow.git

# Install on your site
bench --site your-site-name install-app trackflow

# Run the deployment script
cd apps/trackflow
chmod +x deploy.sh
./deploy.sh your-site-name
```

### Manual Installation

```bash
# If deployment script fails, try manually:
bench --site your-site-name migrate
bench --site your-site-name clear-cache
bench --site your-site-name reload-doctype-cache
bench restart
```

## 🔧 Configuration

### 1. Enable TrackFlow in Sidebar
After installation, TrackFlow should appear in the CRM sidebar. If not visible:
```bash
bench --site your-site-name clear-website-cache
bench --site your-site-name build
```

### 2. Initial Setup
1. Navigate to **TrackFlow > Settings**
2. Configure default attribution model
3. Set up tracking domains
4. Configure notification preferences

### 3. Create First Campaign
1. Go to **TrackFlow > Campaigns > New**
2. Fill in:
   - Campaign Name
   - Type (Email, Social, PPC, etc.)
   - Budget and dates
3. Save

### 4. Generate Tracked Links
```python
# Single link
1. TrackFlow > Tracked Links > New
2. Enter destination URL and campaign
3. Save to get short URL

# Bulk generation
1. Open a Campaign
2. Click "Bulk Generate Links"
3. Enter identifiers (comma-separated)
4. Generate
```

## 📁 Project Structure

```
trackflow/
├── trackflow/
│   ├── api/                    # API endpoints
│   │   ├── __init__.py        ✓ Fixed
│   │   ├── analytics.py
│   │   ├── campaign.py
│   │   ├── links.py           ✓ Working
│   │   ├── tracking.py
│   │   └── visitor.py
│   ├── config/                 # Configuration
│   │   ├── __init__.py        ✓ Added
│   │   └── trackflow.py       ✓ Sidebar config
│   ├── integrations/           # CRM Integration
│   │   ├── crm_lead.py        ✓ Implemented
│   │   ├── crm_deal.py        ✓ Implemented
│   │   ├── crm_organization.py ✓ Implemented
│   │   ├── crm_contact.py     ❌ Missing
│   │   └── web_form.py        ✓ Implemented
│   ├── trackflow/
│   │   └── doctype/           # 30+ DocTypes
│   │       ├── link_campaign/
│   │       ├── tracked_link/
│   │       ├── click_event/
│   │       ├── visitor_session/
│   │       ├── attribution_model/
│   │       └── ... (25+ more)
│   ├── public/                # Frontend assets
│   │   ├── js/
│   │   │   ├── crm_lead.js
│   │   │   ├── crm_deal.js
│   │   │   └── crm_organization.js
│   │   └── css/
│   └── www/                   # Web routes
│       └── redirect.py        ✓ Tracking redirects
├── hooks.py                   ✓ Updated with module config
├── install.py                 # Installation scripts
├── deploy.sh                  ✓ Deployment helper
└── requirements.txt
```

## 🔌 API Endpoints

### Tracking
```javascript
// Get tracking script
GET /api/method/trackflow.api.tracking.get_tracking_script

// Track custom event
POST /api/method/trackflow.api.tracking.track_event
{
  "visitor_id": "uuid",
  "event_type": "custom",
  "event_data": {}
}
```

### Campaign Management
```javascript
// Bulk generate links
POST /api/method/trackflow.api.links.bulk_generate_links
{
  "campaign": "campaign-name",
  "identifiers": "id1,id2,id3"
}

// Get campaign analytics
GET /api/method/trackflow.api.analytics.get_campaign_stats?campaign=name
```

## 🧪 Testing

### Verify Installation
```python
bench --site your-site-name console

# Check if app is installed
frappe.get_installed_apps()
# Should include 'trackflow'

# Test API import
import trackflow.api.links
trackflow.api.links.bulk_generate_links("test", "id1,id2")

# Check for errors
frappe.get_all('Error Log', filters={'method': ['like', '%trackflow%']}, limit=5)
```

### Create Test Data
```python
# In bench console
from trackflow.demo_data import create_demo_data
create_demo_data()
```

## 🐛 Troubleshooting

### TrackFlow not in sidebar
```bash
bench --site your-site-name clear-cache
bench --site your-site-name reload-doctype-cache
bench restart
```

### Module import errors
```bash
# Check Python path
bench --site your-site-name console
import sys
print(sys.path)
# Should include apps/trackflow
```

### Tracking not working
1. Check browser console for JavaScript errors
2. Verify cookies are enabled
3. Check if redirect URLs are accessible: `/r/test`

## 🚧 Roadmap

### High Priority
- [ ] Email tracking (pixel tracking, click tracking)
- [ ] CRM Contact integration
- [ ] Activity/Communication tracking
- [ ] Real-time dashboard

### Medium Priority
- [ ] Multi-currency support
- [ ] Webhook support
- [ ] Advanced segmentation
- [ ] A/B testing for links

### Future
- [ ] WhatsApp/SMS tracking
- [ ] Advanced ML attribution
- [ ] Predictive analytics
- [ ] API v2 with GraphQL

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## 📄 License

MIT License - see LICENSE file

## 👨‍💻 Author

**Chinmay Bhat**  
Email: chinmaybhatk@gmail.com  
GitHub: [@chinmaybhatk](https://github.com/chinmaybhatk)

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/chinmaybhatk/trackflow/issues)
- **Discussions**: [GitHub Discussions](https://github.com/chinmaybhatk/trackflow/discussions)
- **Email**: support@trackflow.app

## ⚠️ Important Notes

1. **Beta Software**: This is beta software. Test thoroughly before production use.
2. **Frappe CRM Only**: Designed for Frappe CRM, not standard ERPNext CRM.
3. **Data Privacy**: Implements visitor tracking - ensure compliance with local privacy laws.
4. **Performance**: For high-traffic sites, consider using Redis for session storage.

---

**Last Technical Update**: September 4, 2025
- Fixed API module imports
- Added sidebar configuration
- Created deployment script
- Updated hooks.py with module registration
