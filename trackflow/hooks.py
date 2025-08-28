app_name = "trackflow"
app_title = "TrackFlow"
app_publisher = "Chinmay Bhat"
app_description = "Smart link tracking and attribution for Frappe CRM"
app_email = "support@trackflow.app"
app_license = "MIT"
app_version = "1.0.0"

# Module Configuration
modules = {
    "TrackFlow": {
        "color": "#2563eb",
        "icon": "fa fa-link",
        "type": "module",
        "label": "TrackFlow",
        "category": "Modules"
    }
}

# Scheduled Tasks (commented out to prevent errors during initial setup)
# scheduler_events = {
#     "hourly": [
#         "trackflow.tasks.process_visitor_sessions",
#         "trackflow.tasks.update_campaign_metrics"
#     ],
#     "daily": [
#         "trackflow.tasks.cleanup_expired_data",
#         "trackflow.tasks.calculate_attribution"
#     ]
# }

# Document Events
doc_events = {
    "CRM Lead": {
        "after_insert": "trackflow.integrations.crm_lead.on_lead_create",
        "on_update": "trackflow.integrations.crm_lead.on_lead_update"
    },
    "CRM Deal": {
        "after_insert": "trackflow.integrations.crm_deal.after_insert",
        "on_update": "trackflow.integrations.crm_deal.on_update"
    }
}

# App Icon and Branding
app_icon = "fa fa-link"
app_color = "#2563eb"
