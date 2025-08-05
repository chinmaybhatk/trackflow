app_name = "trackflow"
app_title = "TrackFlow"
app_publisher = "Chinmay Bhat"
app_description = "Smart link tracking and attribution for Frappe CRM"
app_email = "support@trackflow.app"
app_license = "MIT"
app_version = "1.0.0"

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
    "Lead": "public/js/lead.js",
    "Contact": "public/js/contact.js",
    "Deal": "public/js/deal.js",
    "Opportunity": "public/js/opportunity.js"
}

# Scheduled Tasks
# ---------------
scheduler_events = {
    "hourly": [
        "trackflow.tasks.process_visitor_sessions",
        "trackflow.tasks.update_campaign_metrics"
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

# Jinja Environment
# -----------------
jinja = {
    "methods": "trackflow.utils.jinja_methods",
    "filters": "trackflow.utils.jinja_filters"
}

# Installation
# ------------
before_install = "trackflow.install.before_install"
after_install = "trackflow.install.after_install"
after_migrate = "trackflow.install.after_migrate"

# Fixtures
# --------
fixtures = [
    {
        "dt": "Custom Field",
        "filters": [
            [
                "name",
                "in",
                [
                    "Lead-trackflow_visitor_id",
                    "Lead-trackflow_source",
                    "Lead-trackflow_medium",
                    "Lead-trackflow_campaign",
                    "Lead-trackflow_first_touch_date",
                    "Lead-trackflow_last_touch_date",
                    "Lead-trackflow_touch_count",
                    "Contact-trackflow_visitor_id",
                    "Contact-trackflow_engagement_score",
                    "Contact-trackflow_last_campaign",
                    "Deal-trackflow_attribution_model",
                    "Deal-trackflow_first_touch_source",
                    "Deal-trackflow_last_touch_source",
                    "Deal-trackflow_marketing_influenced",
                    "Opportunity-trackflow_campaign",
                    "Opportunity-trackflow_source"
                ]
            ]
        ]
    },
    {
        "dt": "Property Setter",
        "filters": [
            ["name", "in", ["Lead-main-track_source", "Deal-main-track_attribution"]]
        ]
    }
]

# Document Events
# ---------------
doc_events = {
    "Lead": {
        "after_insert": "trackflow.integrations.lead.after_insert",
        "on_update": "trackflow.integrations.lead.on_update",
        "on_trash": "trackflow.integrations.lead.on_trash"
    },
    "Contact": {
        "after_insert": "trackflow.integrations.contact.after_insert",
        "on_update": "trackflow.integrations.contact.on_update"
    },
    "Deal": {
        "after_insert": "trackflow.integrations.deal.after_insert",
        "on_update": "trackflow.integrations.deal.on_update",
        "on_submit": "trackflow.integrations.deal.calculate_attribution"
    },
    "Opportunity": {
        "on_update": "trackflow.integrations.opportunity.track_opportunity"
    },
    "Web Form": {
        "on_update": "trackflow.integrations.web_form.setup_tracking"
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

# REST API
# --------
rest_api_methods = [
    "trackflow.api.analytics.get_analytics",
    "trackflow.api.campaign.create_campaign",
    "trackflow.api.tracking.track_event"
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

# Custom Workspace
# ----------------
workspace = {
    "TrackFlow": {
        "category": "Modules",
        "color": "#2563eb",
        "icon": "fa fa-link",
        "type": "module",
        "label": "TrackFlow",
        "public": 1,
        "hidden": 0
    }
}
