# TrackFlow - Frappe CRM Integration

## Overview
TrackFlow integrates seamlessly into Frappe CRM, enhancing your existing CRM workflows with powerful link tracking and attribution capabilities.

## Integration Points

### CRM Lead
- **Create Tracking Link**: Generate tracked links directly from lead forms
- **View Attribution**: See complete attribution data for each lead
- **View Journey**: Track the visitor journey from first touch to conversion
- **Link to Campaign**: Associate leads with marketing campaigns

### CRM Deal
- **Calculate Attribution**: Determine which marketing touchpoints influenced the deal
- **View Journey**: See the complete customer journey
- **Attribution Models**: Apply different attribution models (Last Touch, First Touch, Linear, etc.)

### CRM Organization
- **View Engagement**: Track organization-level engagement scores
- **Campaign Analysis**: See which campaigns influenced the organization

### Web Forms
- **Enable Tracking**: Track form submissions and conversions
- **Link to Goals**: Connect forms to campaign goals

## Access TrackFlow Features

1. Open any CRM Lead, Deal, or Organization
2. Look for the "TrackFlow" button group in the form toolbar
3. Use the available options to create tracking links, view attribution, etc.

## Custom Fields Added

TrackFlow adds the following fields to CRM DocTypes:

### CRM Lead
- `trackflow_visitor_id`: Links to visitor tracking data
- `trackflow_source`: Traffic source (e.g., google, facebook)
- `trackflow_medium`: Traffic medium (e.g., organic, cpc, email)
- `trackflow_campaign`: Associated campaign name
- `trackflow_first_touch_date`: Date of first interaction
- `trackflow_last_touch_date`: Date of most recent interaction
- `trackflow_touch_count`: Number of touchpoints

### CRM Deal
- `trackflow_attribution_model`: Selected attribution model
- `trackflow_first_touch_source`: First touchpoint source
- `trackflow_last_touch_source`: Last touchpoint source
- `trackflow_marketing_influenced`: Whether marketing influenced the deal

### CRM Organization
- `trackflow_visitor_id`: Links to visitor tracking data
- `trackflow_engagement_score`: Calculated engagement score
- `trackflow_last_campaign`: Most recent campaign interaction

## No Separate Module

Unlike traditional Frappe apps, TrackFlow doesn't create a separate module or workspace. Instead, it enhances your existing CRM interface with tracking capabilities, maintaining a clean and integrated user experience.

## API Access

TrackFlow APIs are available at:
- `/api/method/trackflow.api.tracking.create_tracking_link`
- `/api/method/trackflow.api.tracking.track_event`
- `/api/method/trackflow.api.analytics.get_analytics`

## Support

For support, please visit: https://github.com/chinmaybhatk/trackflow
