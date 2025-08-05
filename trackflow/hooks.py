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
    "Tracked Link": "trackflow.trackflow.doctype.tracked_link.tracked_link.get_permission_query_conditions",
    "Link Campaign": "trackflow.trackflow.doctype.link_campaign.link_campaign.get_permission_query_conditions",
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
        "trackflow.tasks.process_click_queue"
    ],
    "daily": [
        "trackflow.tasks.cleanup_expired_links",
        "trackflow.tasks.generate_daily_reports"
    ],
    "weekly": [
        "trackflow.tasks.send_weekly_analytics"
    ]
}

# Website Route Rules
# --------------------
website_route_rules = [
    {"from_route": "/tl/<path:short_code>", "to_route": "trackflow.www.redirect.handle_redirect"},
    {"from_route": "/trackflow/dashboard", "to_route": "trackflow.www.dashboard"},
]

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
                    "Lead-trackflow_source",
                    "Lead-trackflow_campaign",
                    "Lead-first_touch_source",
                    "Lead-last_touch_source",
                    "Contact-engagement_score",
                    "Contact-last_campaign_interaction",
                    "Deal-attribution_source",
                    "Deal-marketing_influenced"
                ]
            ]
        ]
    },
    {
        "dt": "Property Setter",
        "filters": [
            ["name", "in", ["Lead-main-track_source"]]
        ]
    }
]

# Document Events
# ---------------
doc_events = {
    "Lead": {
        "after_insert": "trackflow.integrations.lead.after_insert",
        "on_update": "trackflow.integrations.lead.on_update"
    },
    "Deal": {
        "on_update": "trackflow.integrations.deal.track_attribution"
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
app_icon = "octicon octicon-graph"
app_color = "#2563eb"
app_logo_url = "/assets/trackflow/images/trackflow-logo.svg"

# User Data Fields
# ----------------
user_data_fields = [
    {
        "doctype": "Tracked Link",
        "filter_by": "owner",
        "redact_fields": ["ip_address", "user_agent"],
        "partial": 1,
    },
    {
        "doctype": "Click Event",
        "filter_by": "link_owner",
        "strict": False,
    }
]

# Monitoring
# ----------
monitor_jobs = [
    "trackflow.tasks.process_click_queue",
    "trackflow.tasks.update_analytics_cache"
]

# Global Search
# -------------
global_search_doctypes = {
    "Default": [
        {"doctype": "Tracked Link", "index": 0},
        {"doctype": "Link Campaign", "index": 1}
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
    "trackflow.api.create_link",
    "trackflow.api.get_analytics",
    "trackflow.api.track_conversion"
]

# Branding
# --------
brand_html = """<div style='padding: 10px; text-align: center;'>
    <img src='/assets/trackflow/images/trackflow-logo.svg' style='height: 20px; margin-right: 5px;'>
    <span style='font-size: 12px; color: #6b7280;'>Powered by TrackFlow</span>
</div>"""