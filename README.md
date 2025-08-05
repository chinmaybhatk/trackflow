# TrackFlow - Smart Link Tracking and Attribution for Frappe CRM

TrackFlow is a comprehensive marketing attribution and link tracking app for Frappe/ERPNext. It helps businesses track their marketing campaigns, understand customer journeys, and attribute revenue to the right marketing channels.

## Features

### 🔗 Link Tracking
- Create trackable short links with custom UTM parameters
- Track clicks, unique visitors, and conversions
- QR code generation for offline campaigns
- Real-time click analytics

### 📊 Campaign Management
- Create and manage marketing campaigns
- Set goals and track progress
- Budget tracking and ROI calculation
- Multi-channel campaign support

### 🎯 Attribution Modeling
- Multiple attribution models (Last Touch, First Touch, Linear, Time Decay, Position Based)
- Track customer journey from first touch to conversion
- Revenue attribution by campaign
- Deal and opportunity tracking

### 📈 Analytics & Reporting
- Real-time analytics dashboard
- Visitor behavior tracking
- Conversion funnel analysis
- Campaign performance reports
- Custom date range filtering

### 🔌 CRM Integration
- Automatic lead source tracking
- Contact engagement scoring
- Opportunity attribution
- Web form tracking
- Custom field integration

### 🔔 Notifications
- Goal achievement alerts
- Conversion notifications
- Campaign performance alerts
- Email and system notifications

## Installation

### Prerequisites
- Frappe Framework v14 or higher
- ERPNext with CRM module installed

### Install via Bench

```bash
# Navigate to your bench directory
cd ~/frappe-bench

# Get the app
bench get-app https://github.com/chinmaybhatk/trackflow.git

# Install the app to your site
bench --site your-site-name install-app trackflow

# Run migrations
bench --site your-site-name migrate

# Clear cache
bench --site your-site-name clear-cache

# Restart bench
bench restart
```

## Setup

### 1. Initial Configuration
After installation, TrackFlow will:
- Create custom fields in Lead, Contact, Opportunity, and Web Form
- Set up tracking roles (TrackFlow Manager, TrackFlow User)
- Add tracking script to your website
- Create the TrackFlow workspace

### 2. Create Your First Campaign
1. Go to TrackFlow > Campaign > New
2. Enter campaign details:
   - Campaign Name
   - Type (Email, Social, Content, etc.)
   - Budget and expected revenue
   - Start and end dates
3. Add campaign goals
4. Save

### 3. Create Tracking Links
1. Go to TrackFlow > Tracking Link > New
2. Enter:
   - Title for your link
   - Destination URL
   - Select campaign
   - Add UTM parameters (optional)
3. Save to generate tracking link
4. Use the short URL in your marketing materials

### 4. Enable Web Form Tracking
1. Go to any Web Form
2. Check "Enable TrackFlow Tracking"
3. Optionally link to a campaign goal
4. Save

## Usage

### Dashboard
Access the TrackFlow Dashboard from the workspace to see:
- Real-time visitor activity
- Campaign performance metrics
- Recent conversions
- Top performing links

### Reports
- **Campaign Performance**: Overview of all campaigns
- **Visitor Analytics**: Detailed visitor behavior analysis
- **Conversion Funnel**: Visualize your conversion process

### API Integration

#### Tracking Script
The tracking script is automatically included on your website. You can also manually include it:

```html
<script src="/api/method/trackflow.api.tracking.get_tracking_script" async></script>
```

#### Track Custom Events
```javascript
// Track custom events
TrackFlow.track('custom_event', {
    category: 'video',
    action: 'play',
    label: 'product-demo'
});
```

#### Server-side Tracking
```python
import requests

# Track server-side events
response = requests.post('https://your-site.com/api/method/trackflow.api.track_event', {
    'visitor_id': 'visitor-uuid',
    'event_type': 'purchase',
    'event_data': {
        'value': 99.99,
        'currency': 'USD'
    }
})
```

## Demo Data

To create demo data for testing:

```python
# In bench console
bench --site your-site-name console

# Import and run demo data creation
from trackflow.trackflow.demo_data import create_demo_data
create_demo_data()
```

To clear demo data:
```python
from trackflow.trackflow.demo_data import clear_demo_data
clear_demo_data()
```

## Attribution Models

TrackFlow supports multiple attribution models:

1. **Last Touch**: 100% credit to the last interaction
2. **First Touch**: 100% credit to the first interaction
3. **Linear**: Equal credit to all touchpoints
4. **Time Decay**: More credit to recent interactions
5. **Position Based**: 40% first, 40% last, 20% middle

## Customization

### Custom Fields
TrackFlow adds custom fields to track attribution data. You can find these in:
- Lead: Visitor ID, source, medium, campaign, touchpoint data
- Contact: Visitor ID, engagement score
- Opportunity: Campaign attribution, marketing influence
- Web Form: Tracking settings

### Permissions
Two default roles are created:
- **TrackFlow Manager**: Full access to all features
- **TrackFlow User**: Can create and view, limited delete access

## Troubleshooting

### Tracking not working
1. Check if tracking script is loaded on your website
2. Verify cookies are enabled
3. Check browser console for errors

### Missing data
1. Clear cache: `bench --site your-site-name clear-cache`
2. Run migrations: `bench --site your-site-name migrate`
3. Check error logs: `bench --site your-site-name console`

## Development

### Project Structure
```
trackflow/
├── trackflow/
│   ├── doctype/           # DocType definitions
│   ├── report/            # Reports
│   ├── page/              # Pages
│   ├── api/               # API endpoints
│   ├── integrations/      # CRM integrations
│   └── utils.py           # Utility functions
├── hooks.py               # App hooks
├── install.py             # Installation scripts
└── requirements.txt       # Python dependencies
```

### Contributing
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see LICENSE file for details

## Support

For issues, questions, or contributions:
- GitHub Issues: https://github.com/chinmaybhatk/trackflow/issues
- Email: support@trackflow.app

## Credits

Created and maintained by Chinmay Bhat

---

**Note**: This is an open-source project. Use at your own risk. Always test in a development environment before deploying to production.
