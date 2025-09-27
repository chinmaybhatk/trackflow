app_name = "trackflow"
app_title = "TrackFlow"
app_publisher = "Chinmay Bhat"
app_description = "Smart link tracking and attribution for Frappe CRM"
app_email = "support@trackflow.app"
app_license = "MIT"
app_version = "1.0.1"

# Add module configuration for CRM integration
# Module definitions should be handled by module.py files in each module directory

# Include files for CRM integration
app_include_css = "/assets/trackflow/css/trackflow.css"
app_include_js = "/assets/trackflow/js/trackflow.js"

# DocType JavaScript for CRM integration
doctype_js = {
    "CRM Lead": "public/js/crm_lead.js",
    "CRM Deal": "public/js/crm_deal.js", 
    "CRM Organization": "public/js/crm_organization.js",
    "Web Form": "public/js/web_form.js"
}

# DocType CSS
doctype_list_js = {
    "CRM Lead": "public/js/crm_lead_list.js"
}

# Document Events
doc_events = {
    "CRM Lead": {
        "after_insert": "trackflow.integrations.crm_lead.on_lead_create",
        "on_update": "trackflow.integrations.crm_lead.on_lead_update",
        "on_trash": "trackflow.integrations.crm_lead.on_lead_trash"
    },
    "CRM Organization": {
        "after_insert": "trackflow.integrations.crm_organization.after_insert",
        "on_update": "trackflow.integrations.crm_organization.on_update"
    },
    "CRM Deal": {
        "after_insert": "trackflow.integrations.crm_deal.after_insert",
        "on_update": "trackflow.integrations.crm_deal.on_update",
        "on_submit": "trackflow.integrations.crm_deal.calculate_attribution"
    },
    "Web Form": {
        "on_update": "trackflow.integrations.web_form.inject_tracking_script",
        "validate": "trackflow.integrations.web_form.validate_tracking_settings"
    }
}

# Scheduled Tasks
scheduler_events = {
    "hourly": [
        "trackflow.tasks.process_visitor_sessions",
        "trackflow.tasks.update_campaign_metrics",
        "trackflow.notifications.check_campaign_performance"
    ],
    "daily": [
        "trackflow.tasks.cleanup_expired_data",
        "trackflow.tasks.generate_daily_reports",
        "trackflow.tasks.calculate_attribution"
    ],
    "weekly": [
        "trackflow.tasks.send_weekly_analytics",
        "trackflow.tasks.cleanup_old_visitors"
    ]
}

# Installation hooks
before_install = "trackflow.install.before_install"
after_install = "trackflow.install.after_install"
after_migrate = "trackflow.install.after_migrate"

# Whitelisted Methods for API
override_whitelisted_methods = {
    "frappe.www.contact.send_message": "trackflow.overrides.contact.track_form_submission"
}

# Website tracking
website_route_rules = [
    {"from_route": "/r/<path:tracking_id>", "to_route": "trackflow.www.redirect.handle_redirect"},
    {"from_route": "/t/<path:tracking_id>", "to_route": "trackflow.www.redirect.handle_redirect"}
]

before_request = ["trackflow.www.redirect.before_request"]
after_request = ["trackflow.tracking.after_request"]

# REST API Methods - These should be whitelisted in the respective modules
# API methods are exposed through @frappe.whitelist() decorators in the respective files

# Permissions
permission_query_conditions = {
    "Tracked Link": "trackflow.trackflow.doctype.tracked_link.tracked_link.get_permission_query_conditions",
    "Link Campaign": "trackflow.trackflow.doctype.link_campaign.link_campaign.get_permission_query_conditions"
}

# Fixtures - Include custom fields and roles
fixtures = [
    {
        "dt": "Custom Field",
        "filters": [
            [
                "name",
                "in",
                [
                    "CRM Lead-trackflow_visitor_id",
                    "CRM Lead-trackflow_source",
                    "CRM Lead-trackflow_medium",
                    "CRM Lead-trackflow_campaign",
                    "CRM Lead-trackflow_first_touch_date",
                    "CRM Lead-trackflow_last_touch_date",
                    "CRM Lead-trackflow_touch_count",
                    "CRM Lead-trackflow_tab",
                    "CRM Organization-trackflow_visitor_id",
                    "CRM Organization-trackflow_engagement_score",
                    "CRM Organization-trackflow_last_campaign",
                    "CRM Deal-trackflow_attribution_model",
                    "CRM Deal-trackflow_first_touch_source",
                    "CRM Deal-trackflow_last_touch_source",
                    "CRM Deal-trackflow_marketing_influenced",
                    "Web Form-trackflow_tracking_enabled",
                    "Web Form-trackflow_conversion_goal"
                ]
            ]
        ]
    },
    "trackflow/fixtures/roles.json",
    "trackflow/fixtures/crm_workspace_extension.json"
]

# App Icon
app_icon = "fa fa-link"
app_color = "#2563eb"

# For Frappe CRM Integration
has_web_view = 1

# For Frappe CRM Integration - Frontend Override
# This allows TrackFlow to appear in CRM sidebar
extend_bootinfo = ["trackflow.boot.bootinfo"]

# Override CRM workspace to include TrackFlow
# Temporarily disabled due to compatibility issues with Frappe v15
# override_doctype_dashboards = {
#     "CRM Lead": "trackflow.dashboard.crm_lead_dashboard",
#     "CRM Deal": "trackflow.dashboard.crm_deal_dashboard"
# }
