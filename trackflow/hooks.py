app_name = "trackflow"
app_title = "TrackFlow"
app_publisher = "Chinmay Bhat"
app_description = "Smart link tracking and attribution for Frappe CRM"
app_email = "support@trackflow.app"
app_license = "MIT"
app_version = "1.0.0"

# Required for sidebar visibility
has_permission = {"TrackFlow": "trackflow.permissions.has_app_permission"}

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

# Include files
# ------------------

# include js, css files in header of desk.html
app_include_css = "/assets/trackflow/css/trackflow.css"
app_include_js = "/assets/trackflow/js/trackflow.js"

# include js, css files in header of web template
web_include_css = "/assets/trackflow/css/trackflow-web.css"
web_include_js = "/assets/trackflow/js/trackflow-web.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "trackflow/public/scss/website"

# Desk Notifications
# ------------------
notification_config = "trackflow.notifications.get_notification_config"

# Permissions
# -----------
permission_query_conditions = {
    "Tracking Link": "trackflow.trackflow.doctype.tracking_link.tracking_link.get_permission_query_conditions",
    "Campaign": "trackflow.trackflow.doctype.campaign.campaign.get_permission_query_conditions",
}

# DocType JavaScript
# ------------------
doctype_js = {
    "CRM Lead": "public/js/crm_lead.js",
    "CRM Organization": "public/js/crm_organization.js",
    "CRM Deal": "public/js/crm_deal.js",
    "Web Form": "public/js/web_form.js"
}

# Scheduled Tasks
# ---------------
scheduler_events = {
    "hourly": [
        "trackflow.tasks.process_visitor_sessions",
        "trackflow.tasks.update_campaign_metrics",
        "trackflow.notifications.check_campaign_performance"
    ],
    "daily": [
        "trackflow.tasks.cleanup_expired_data",
        "trackflow.tasks.generate_daily_reports",
        "trackflow.tasks.calculate_attribution",
        "trackflow.tasks.update_visitor_profiles"
    ],
    "weekly": [
        "trackflow.tasks.send_weekly_analytics",
        "trackflow.tasks.cleanup_old_visitors",
        "trackflow.tasks.generate_attribution_reports"
    ]
}

# Website Route Rules
# --------------------
website_route_rules = [
    {"from_route": "/r/<path:tracking_id>", "to_route": "trackflow.www.redirect.handle_redirect"},
    {"from_route": "/t/<path:tracking_id>", "to_route": "trackflow.www.redirect.handle_redirect"},
    {"from_route": "/trackflow/dashboard", "to_route": "trackflow.www.dashboard"},
    {"from_route": "/trackflow/pixel/<path:visitor_id>", "to_route": "trackflow.www.pixel"},
]

# Request Handler
# ---------------
before_request = ["trackflow.www.redirect.before_request"]
# Re-enabled after fixing error handling
after_request = ["trackflow.tracking.after_request"]

# Jinja Environment
# -----------------
# Temporarily disabled jinja hooks to isolate error
# jinja = {
#     "methods": "trackflow.utils.jinja_methods",
#     "filters": "trackflow.utils.jinja_filters"
# }

# Installation
# ------------
before_install = "trackflow.install.before_install"
after_install = "trackflow.install.after_install"
after_migrate = "trackflow.install.after_migrate"

# Fixtures
# --------
fixtures = [
    {
        "dt": "Workspace",
        "filters": [["name", "=", "TrackFlow"]]
    },
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
    {
        "dt": "Property Setter",
        "filters": [
            ["name", "in", ["CRM Lead-main-track_source", "CRM Deal-main-track_attribution"]]
        ]
    }
]

# Document Events
# ---------------
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
    },
    "*": {
        "after_insert": "trackflow.integrations.web_form.on_web_form_submit"
    }
}

# Override Whitelisted Methods
# ----------------------------
override_whitelisted_methods = {
    "frappe.www.contact.send_message": "trackflow.overrides.track_form_submission"
}

# Authentication Hooks
# --------------------
# auth_hooks = ["trackflow.auth.validate"]

# App Icon and Branding
# ---------------------
app_icon = "fa fa-link"
app_color = "#2563eb"
app_logo_url = "/assets/trackflow/images/trackflow-logo.svg"

# User Data Fields
# ----------------
user_data_fields = [
    {
        "doctype": "Tracking Link",
        "filter_by": "owner",
        "redact_fields": ["last_accessed_ip"],
        "partial": 1,
    },
    {
        "doctype": "Visitor",
        "filter_by": "owner",
        "strict": False,
    }
]

# Monitoring
# ----------
monitor_jobs = [
    "trackflow.tasks.process_visitor_sessions",
    "trackflow.tasks.calculate_attribution"
]

# Global Search
# -------------
global_search_doctypes = {
    "Default": [
        {"doctype": "Tracking Link", "index": 0},
        {"doctype": "Campaign", "index": 1},
        {"doctype": "Visitor", "index": 2}
    ]
}

# Website Context
# ---------------
website_context = {
    "favicon": "/assets/trackflow/images/favicon.png",
    "splash_image": "/assets/trackflow/images/splash.png"
}

update_website_context = "trackflow.integrations.web_form.inject_tracking_script"

# REST API
# --------
rest_api_methods = [
    "trackflow.api.analytics.get_analytics",
    "trackflow.api.campaign.create_campaign",
    "trackflow.api.tracking.track_event",
    "trackflow.api.tracking.get_tracking_script",
    "trackflow.api.visitor.get_visitor_profile",
    # Debug endpoints
    "trackflow.api.debug.test",
    "trackflow.api.debug.debug",
    "trackflow.api.debug.diagnose_error"
]

# Branding
# --------
brand_html = """<div style='padding: 10px; text-align: center;'>
    <img src='/assets/trackflow/images/trackflow-logo.svg' style='height: 20px; margin-right: 5px;'>
    <span style='font-size: 12px; color: #6b7280;'>Powered by TrackFlow</span>
</div>"""

# Additional API endpoints
# ------------------------
website_apis = [
    "trackflow.api.pixel",
    "trackflow.api.track"
]

# Workspace config
# ----------------
workspaces = {
    "TrackFlow": "trackflow/trackflow/workspace/trackflow/trackflow.json"
}

# Menu items that appear in the portal
standard_portal_menu_items = [
    {"title": "TrackFlow Dashboard", "route": "/trackflow", "reference_doctype": "TrackFlow Settings", "role": "TrackFlow User"}
]
