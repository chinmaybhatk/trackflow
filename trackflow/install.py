# -*- coding: utf-8 -*-
# Copyright (c) 2024, TrackFlow and contributors
# For license information, please see license.txt

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.custom.doctype.property_setter.property_setter import make_property_setter


def after_install():
    """Called after TrackFlow is installed."""
    print("Setting up TrackFlow...")
    
    # Create custom fields
    create_custom_fields(get_custom_fields())
    
    # Create notification templates
    create_notification_templates()
    
    # Set up roles and permissions
    setup_roles_and_permissions()
    
    # Create initial settings
    create_initial_settings()
    
    # Create workspace
    create_workspace()
    
    # Commit changes
    frappe.db.commit()
    print("TrackFlow setup completed!")


def get_custom_fields():
    """Get custom field definitions for various doctypes."""
    return {
        "Lead": [
            {
                "fieldname": "trackflow_section",
                "label": "TrackFlow",
                "fieldtype": "Section Break",
                "insert_after": "blog_subscriber",
                "collapsible": 1
            },
            {
                "fieldname": "trackflow_source",
                "label": "TrackFlow Source",
                "fieldtype": "Data",
                "insert_after": "trackflow_section",
                "read_only": 1
            },
            {
                "fieldname": "trackflow_campaign",
                "label": "Campaign",
                "fieldtype": "Link",
                "options": "Link Campaign",
                "insert_after": "trackflow_source",
                "read_only": 1
            },
            {
                "fieldname": "trackflow_medium",
                "label": "Medium",
                "fieldtype": "Data",
                "insert_after": "trackflow_campaign",
                "read_only": 1
            },
            {
                "fieldname": "trackflow_content",
                "label": "Content",
                "fieldtype": "Data",
                "insert_after": "trackflow_medium",
                "read_only": 1
            },
            {
                "fieldname": "trackflow_term",
                "label": "Term",
                "fieldtype": "Data",
                "insert_after": "trackflow_content",
                "read_only": 1
            },
            {
                "fieldname": "trackflow_col",
                "label": "",
                "fieldtype": "Column Break",
                "insert_after": "trackflow_term"
            },
            {
                "fieldname": "trackflow_first_click",
                "label": "First Click",
                "fieldtype": "Datetime",
                "insert_after": "trackflow_col",
                "read_only": 1
            },
            {
                "fieldname": "trackflow_last_click",
                "label": "Last Click",
                "fieldtype": "Datetime",
                "insert_after": "trackflow_first_click",
                "read_only": 1
            },
            {
                "fieldname": "trackflow_click_count",
                "label": "Click Count",
                "fieldtype": "Int",
                "insert_after": "trackflow_last_click",
                "read_only": 1,
                "default": 0
            },
            {
                "fieldname": "trackflow_conversion_value",
                "label": "Conversion Value",
                "fieldtype": "Currency",
                "insert_after": "trackflow_click_count",
                "read_only": 1
            }
        ],
        "Contact": [
            {
                "fieldname": "trackflow_section",
                "label": "TrackFlow",
                "fieldtype": "Section Break",
                "insert_after": "sync_with_google_contacts",
                "collapsible": 1
            },
            {
                "fieldname": "trackflow_source",
                "label": "TrackFlow Source",
                "fieldtype": "Data",
                "insert_after": "trackflow_section",
                "read_only": 1
            },
            {
                "fieldname": "trackflow_campaign",
                "label": "Campaign",
                "fieldtype": "Link",
                "options": "Link Campaign",
                "insert_after": "trackflow_source",
                "read_only": 1
            },
            {
                "fieldname": "trackflow_medium",
                "label": "Medium",
                "fieldtype": "Data",
                "insert_after": "trackflow_campaign",
                "read_only": 1
            },
            {
                "fieldname": "trackflow_content",
                "label": "Content",
                "fieldtype": "Data",
                "insert_after": "trackflow_medium",
                "read_only": 1
            },
            {
                "fieldname": "trackflow_col",
                "label": "",
                "fieldtype": "Column Break",
                "insert_after": "trackflow_content"
            },
            {
                "fieldname": "trackflow_first_click",
                "label": "First Click",
                "fieldtype": "Datetime",
                "insert_after": "trackflow_col",
                "read_only": 1
            },
            {
                "fieldname": "trackflow_last_click",
                "label": "Last Click",
                "fieldtype": "Datetime",
                "insert_after": "trackflow_first_click",
                "read_only": 1
            },
            {
                "fieldname": "trackflow_click_count",
                "label": "Click Count",
                "fieldtype": "Int",
                "insert_after": "trackflow_last_click",
                "read_only": 1,
                "default": 0
            },
            {
                "fieldname": "trackflow_engagement_score",
                "label": "Engagement Score",
                "fieldtype": "Float",
                "insert_after": "trackflow_click_count",
                "read_only": 1,
                "precision": 2
            }
        ],
        "Opportunity": [
            {
                "fieldname": "trackflow_section",
                "label": "TrackFlow Attribution",
                "fieldtype": "Section Break",
                "insert_after": "contact_by",
                "collapsible": 1
            },
            {
                "fieldname": "trackflow_source",
                "label": "Original Source",
                "fieldtype": "Data",
                "insert_after": "trackflow_section",
                "read_only": 1
            },
            {
                "fieldname": "trackflow_campaign",
                "label": "Campaign",
                "fieldtype": "Link",
                "options": "Link Campaign",
                "insert_after": "trackflow_source",
                "read_only": 1
            },
            {
                "fieldname": "trackflow_attribution_model",
                "label": "Attribution Model",
                "fieldtype": "Link",
                "options": "Attribution Model",
                "insert_after": "trackflow_campaign"
            },
            {
                "fieldname": "trackflow_col",
                "label": "",
                "fieldtype": "Column Break",
                "insert_after": "trackflow_attribution_model"
            },
            {
                "fieldname": "trackflow_touchpoints",
                "label": "Total Touchpoints",
                "fieldtype": "Int",
                "insert_after": "trackflow_col",
                "read_only": 1,
                "default": 0
            },
            {
                "fieldname": "trackflow_attributed_value",
                "label": "Attributed Value",
                "fieldtype": "Currency",
                "insert_after": "trackflow_touchpoints",
                "read_only": 1
            },
            {
                "fieldname": "trackflow_conversion_path",
                "label": "Conversion Path",
                "fieldtype": "Small Text",
                "insert_after": "trackflow_attributed_value",
                "read_only": 1
            }
        ],
        # For compatibility with different CRM versions
        "Deal": [
            {
                "fieldname": "trackflow_section",
                "label": "TrackFlow Attribution",
                "fieldtype": "Section Break",
                "insert_after": "description",
                "collapsible": 1
            },
            {
                "fieldname": "trackflow_source",
                "label": "Original Source",
                "fieldtype": "Data",
                "insert_after": "trackflow_section",
                "read_only": 1
            },
            {
                "fieldname": "trackflow_campaign",
                "label": "Campaign",
                "fieldtype": "Link",
                "options": "Link Campaign",
                "insert_after": "trackflow_source",
                "read_only": 1
            },
            {
                "fieldname": "trackflow_attribution_model",
                "label": "Attribution Model",
                "fieldtype": "Link",
                "options": "Attribution Model",
                "insert_after": "trackflow_campaign"
            },
            {
                "fieldname": "trackflow_col",
                "label": "",
                "fieldtype": "Column Break",
                "insert_after": "trackflow_attribution_model"
            },
            {
                "fieldname": "trackflow_touchpoints",
                "label": "Total Touchpoints",
                "fieldtype": "Int",
                "insert_after": "trackflow_col",
                "read_only": 1,
                "default": 0
            },
            {
                "fieldname": "trackflow_attributed_value",
                "label": "Attributed Value",
                "fieldtype": "Currency",
                "insert_after": "trackflow_touchpoints",
                "read_only": 1
            },
            {
                "fieldname": "trackflow_conversion_path",
                "label": "Conversion Path",
                "fieldtype": "Small Text",
                "insert_after": "trackflow_attributed_value",
                "read_only": 1
            }
        ]
    }


def create_notification_templates():
    """Create notification templates for TrackFlow events."""
    notifications = [
        {
            "name": "TrackFlow Link Clicked",
            "subject": "Link Click Alert: {{ campaign }}",
            "message": """
<p>A tracked link has been clicked!</p>
<br>
<p><strong>Campaign:</strong> {{ campaign }}</p>
<p><strong>Link:</strong> {{ link_url }}</p>
<p><strong>Clicked by:</strong> {{ identifier or 'Anonymous' }}</p>
<p><strong>Location:</strong> {{ city }}, {{ country }}</p>
<p><strong>Device:</strong> {{ device }}</p>
<p><strong>Time:</strong> {{ click_time }}</p>
<br>
<p><a href="{{ link }}">View Details</a></p>
"""
        },
        {
            "name": "TrackFlow Campaign Milestone",
            "subject": "Campaign Milestone: {{ campaign }} - {{ milestone }} clicks!",
            "message": """
<p>Congratulations! Your campaign has reached a milestone.</p>
<br>
<p><strong>Campaign:</strong> {{ campaign }}</p>
<p><strong>Total Clicks:</strong> {{ total_clicks }}</p>
<p><strong>Unique Clicks:</strong> {{ unique_clicks }}</p>
<p><strong>Conversion Rate:</strong> {{ conversion_rate }}%</p>
<br>
<p><a href="{{ link }}">View Campaign Dashboard</a></p>
"""
        },
        {
            "name": "TrackFlow Lead Created",
            "subject": "New Lead from TrackFlow: {{ lead_name }}",
            "message": """
<p>A new lead has been created from a tracked link!</p>
<br>
<p><strong>Lead:</strong> {{ lead_name }}</p>
<p><strong>Email:</strong> {{ email }}</p>
<p><strong>Campaign:</strong> {{ campaign }}</p>
<p><strong>Source:</strong> {{ source }}</p>
<p><strong>Medium:</strong> {{ medium }}</p>
<br>
<p><a href="{{ link }}">View Lead</a></p>
"""
        }
    ]
    
    for notification in notifications:
        if not frappe.db.exists("Email Template", notification["name"]):
            frappe.get_doc({
                "doctype": "Email Template",
                "name": notification["name"],
                "subject": notification["subject"],
                "response": notification["message"],
                "use_html": 1
            }).insert(ignore_permissions=True)


def setup_roles_and_permissions():
    """Set up roles and permissions for TrackFlow."""
    # Create TrackFlow Manager role
    if not frappe.db.exists("Role", "TrackFlow Manager"):
        frappe.get_doc({
            "doctype": "Role",
            "role_name": "TrackFlow Manager",
            "desk_access": 1
        }).insert(ignore_permissions=True)
    
    # Create TrackFlow User role
    if not frappe.db.exists("Role", "TrackFlow User"):
        frappe.get_doc({
            "doctype": "Role",
            "role_name": "TrackFlow User",
            "desk_access": 1
        }).insert(ignore_permissions=True)
    
    # Set permissions for roles
    doctypes_permissions = {
        "TrackFlow Manager": {
            "read": 1,
            "write": 1,
            "create": 1,
            "delete": 1,
            "submit": 1,
            "cancel": 1,
            "amend": 1,
            "report": 1,
            "export": 1,
            "import": 1,
            "share": 1,
            "print": 1,
            "email": 1
        },
        "TrackFlow User": {
            "read": 1,
            "write": 1,
            "create": 1,
            "delete": 0,
            "submit": 0,
            "cancel": 0,
            "amend": 0,
            "report": 1,
            "export": 1,
            "import": 0,
            "share": 1,
            "print": 1,
            "email": 1
        }
    }
    
    trackflow_doctypes = [
        "Tracked Link",
        "Link Campaign",
        "Click Event",
        "Link Template",
        "TrackFlow Settings",
        "Domain Configuration",
        "Attribution Model",
        "Link Conversion",
        "TrackFlow API Key"
    ]
    
    for doctype in trackflow_doctypes:
        for role, perms in doctypes_permissions.items():
            add_permission(doctype, role, perms)


def add_permission(doctype, role, perms):
    """Add permission for a role on a doctype."""
    if not frappe.db.exists("Custom DocPerm", {"parent": doctype, "role": role}):
        doc = frappe.new_doc("Custom DocPerm")
        doc.parent = doctype
        doc.parenttype = "DocType"
        doc.parentfield = "permissions"
        doc.role = role
        
        for perm, value in perms.items():
            setattr(doc, perm, value)
        
        try:
            doc.insert(ignore_permissions=True)
        except:
            # In case Custom DocPerm doesn't exist, use regular DocPerm
            pass


def create_initial_settings():
    """Create initial TrackFlow settings."""
    if not frappe.db.exists("TrackFlow Settings", "TrackFlow Settings"):
        settings = frappe.new_doc("TrackFlow Settings")
        settings.enable_trackflow = 1
        settings.default_redirect_delay = 0
        settings.enable_geolocation = 1
        settings.enable_bot_detection = 1
        settings.cookie_duration = 30
        settings.enable_email_notifications = 0
        settings.link_expiry_days = 365
        settings.enable_link_preview = 1
        settings.track_anonymous_clicks = 1
        settings.auto_create_contacts = 0
        settings.insert(ignore_permissions=True)
    
    # Create default attribution models
    attribution_models = [
        {
            "name": "First Click",
            "model_type": "First Click",
            "description": "Attributes 100% of the conversion value to the first touchpoint"
        },
        {
            "name": "Last Click",
            "model_type": "Last Click", 
            "description": "Attributes 100% of the conversion value to the last touchpoint"
        },
        {
            "name": "Linear",
            "model_type": "Linear",
            "description": "Distributes conversion value equally across all touchpoints"
        },
        {
            "name": "Time Decay",
            "model_type": "Time Decay",
            "description": "Gives more credit to touchpoints closer to conversion",
            "decay_days": 7
        },
        {
            "name": "Position Based",
            "model_type": "Position Based",
            "description": "40% to first, 40% to last, 20% distributed among middle touchpoints",
            "first_touch_weight": 40,
            "last_touch_weight": 40
        }
    ]
    
    for model in attribution_models:
        if not frappe.db.exists("Attribution Model", model["name"]):
            doc = frappe.new_doc("Attribution Model")
            for key, value in model.items():
                setattr(doc, key, value)
            doc.insert(ignore_permissions=True)


def create_workspace():
    """Create TrackFlow workspace."""
    if not frappe.db.exists("Workspace", "TrackFlow"):
        workspace = frappe.new_doc("Workspace")
        workspace.name = "TrackFlow"
        workspace.label = "TrackFlow"
        workspace.icon = "link"
        workspace.restrict_to_domain = ""
        workspace.onboarding = ""
        workspace.module = "TrackFlow"
        workspace.category = "Modules"
        workspace.is_standard = 1
        workspace.extends_another_page = 0
        workspace.is_default = 0
        workspace.is_hidden = 0
        workspace.pin_to_top = 0
        workspace.pin_to_bottom = 0
        
        # Add links
        workspace.links = [
            {
                "type": "Page",
                "label": "Dashboard",
                "icon": "chart",
                "description": "TrackFlow Analytics Dashboard",
                "onboard": 0,
                "is_query_report": 0,
                "link_to": "trackflow-dashboard",
                "link_type": "Page"
            },
            {
                "type": "DocType",
                "label": "Campaigns",
                "icon": "campaign",
                "description": "Manage link campaigns",
                "onboard": 1,
                "link_to": "Link Campaign",
                "link_type": "DocType"
            },
            {
                "type": "DocType",
                "label": "Tracked Links",
                "icon": "link",
                "description": "View and manage tracked links",
                "onboard": 0,
                "link_to": "Tracked Link",
                "link_type": "DocType"
            },
            {
                "type": "DocType",
                "label": "Link Templates",
                "icon": "template",
                "description": "Create reusable link templates",
                "onboard": 0,
                "link_to": "Link Template",
                "link_type": "DocType"
            },
            {
                "type": "Report",
                "label": "Campaign Performance",
                "icon": "report",
                "description": "Detailed campaign analytics",
                "onboard": 0,
                "is_query_report": 1,
                "link_to": "Campaign Performance Report",
                "link_type": "Report",
                "link_doctype": "Link Campaign"
            },
            {
                "type": "Report",
                "label": "Link Analytics",
                "icon": "analytics",
                "description": "Link click analytics",
                "onboard": 0,
                "is_query_report": 1,
                "link_to": "Link Analytics Report",
                "link_type": "Report",
                "link_doctype": "Tracked Link"
            },
            {
                "type": "DocType",
                "label": "Click Events",
                "icon": "click",
                "description": "View all click events",
                "onboard": 0,
                "link_to": "Click Event",
                "link_type": "DocType"
            },
            {
                "type": "DocType",
                "label": "Attribution Models",
                "icon": "flow",
                "description": "Configure attribution models",
                "onboard": 0,
                "link_to": "Attribution Model",
                "link_type": "DocType"
            },
            {
                "type": "DocType",
                "label": "Settings",
                "icon": "setting",
                "description": "TrackFlow configuration",
                "onboard": 1,
                "link_to": "TrackFlow Settings",
                "link_type": "DocType"
            }
        ]
        
        workspace.insert(ignore_permissions=True)
        
        # Add to app modules
        if not frappe.db.exists("Module Onboarding", "TrackFlow"):
            onboarding = frappe.new_doc("Module Onboarding")
            onboarding.module = "TrackFlow"
            onboarding.title = "Get Started with TrackFlow"
            onboarding.subtitle = "Link tracking and attribution for Frappe CRM"
            onboarding.is_complete = 0
            onboarding.steps = [
                {
                    "step": "Configure Settings",
                    "description": "Set up your TrackFlow configuration",
                    "action": "Go to TrackFlow Settings",
                    "is_complete": 0,
                    "is_mandatory": 1
                },
                {
                    "step": "Create First Campaign",
                    "description": "Create your first link tracking campaign",
                    "action": "Create Link Campaign",
                    "is_complete": 0,
                    "is_mandatory": 1
                },
                {
                    "step": "Generate Tracked Link",
                    "description": "Create your first tracked link",
                    "action": "Create Tracked Link",
                    "is_complete": 0,
                    "is_mandatory": 0
                }
            ]
            onboarding.insert(ignore_permissions=True)


def before_uninstall():
    """Cleanup before uninstalling TrackFlow."""
    print("Cleaning up TrackFlow...")
    
    # Remove custom fields
    custom_fields = frappe.get_all("Custom Field", 
        filters={"fieldname": ["like", "trackflow_%"]})
    
    for field in custom_fields:
        frappe.delete_doc("Custom Field", field.name, ignore_permissions=True)
    
    # Remove workspace
    if frappe.db.exists("Workspace", "TrackFlow"):
        frappe.delete_doc("Workspace", "TrackFlow", ignore_permissions=True)
    
    # Remove notification templates
    templates = [
        "TrackFlow Link Clicked",
        "TrackFlow Campaign Milestone", 
        "TrackFlow Lead Created"
    ]
    
    for template in templates:
        if frappe.db.exists("Email Template", template):
            frappe.delete_doc("Email Template", template, ignore_permissions=True)
    
    frappe.db.commit()
    print("TrackFlow cleanup completed!")
