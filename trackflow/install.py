import frappe
from frappe import _
from trackflow.trackflow.custom_fields import create_custom_fields, create_property_setters

def before_install():
    """Tasks to run before installing TrackFlow"""
    print("Preparing TrackFlow installation...")
    
    # Check dependencies
    check_dependencies()
    
    # Create required roles
    create_roles()

def after_install():
    """Tasks to run after installing TrackFlow"""
    print("Setting up TrackFlow...")
    
    # Create custom fields for FCRM
    create_fcrm_custom_fields()
    
    # Create property setters
    create_fcrm_property_setters()
    
    # Create default data
    create_default_data()
    
    # Set up permissions
    setup_permissions()
    
    # Create workspace
    create_workspace()
    
    # Enable tracking
    enable_tracking()
    
    print("TrackFlow installation completed!")
    frappe.msgprint(_("TrackFlow has been successfully installed!"), indicator="green")

def after_migrate():
    """Tasks to run after migration"""
    # Update custom fields if needed
    create_fcrm_custom_fields()
    
    # Update workspace
    update_workspace()

def check_dependencies():
    """Check if required modules are installed"""
    installed_apps = frappe.get_installed_apps()
    missing = []
    
    # Check for Frappe CRM app
    if "crm" not in [app.lower() for app in installed_apps]:
        missing.append("Frappe CRM")
    else:
        # Verify FCRM DocTypes exist
        required_doctypes = ["CRM Lead", "CRM Deal", "CRM Organization"]
        for doctype in required_doctypes:
            if not frappe.db.exists("DocType", doctype):
                missing.append(f"FCRM DocType: {doctype}")
    
    if missing:
        frappe.throw(_("TrackFlow requires the following: {0}").format(", ".join(missing)))

def create_roles():
    """Create roles required for TrackFlow"""
    roles = [
        {
            "role_name": "TrackFlow Manager",
            "desk_access": 1,
            "two_factor_auth": 0,
            "search_bar": 1,
            "notifications": 1,
            "list_sidebar": 1,
            "bulk_actions": 1,
            "view_switcher": 1,
            "form_sidebar": 1,
            "timeline": 1,
            "dashboard": 1
        },
        {
            "role_name": "TrackFlow User",
            "desk_access": 1,
            "two_factor_auth": 0,
            "search_bar": 1,
            "notifications": 1,
            "list_sidebar": 1,
            "bulk_actions": 0,
            "view_switcher": 1,
            "form_sidebar": 1,
            "timeline": 1,
            "dashboard": 1
        }
    ]
    
    for role_data in roles:
        if not frappe.db.exists("Role", role_data["role_name"]):
            role = frappe.new_doc("Role")
            role.update(role_data)
            role.insert()
            print(f"Created role: {role_data['role_name']}")

def create_fcrm_custom_fields():
    """Create custom fields for FCRM DocTypes"""
    custom_fields = {
        "CRM Lead": [
            {
                "fieldname": "trackflow_visitor_id",
                "label": "TrackFlow Visitor ID",
                "fieldtype": "Data",
                "insert_after": "email",
                "read_only": 1
            },
            {
                "fieldname": "trackflow_source",
                "label": "Source",
                "fieldtype": "Data",
                "insert_after": "trackflow_visitor_id"
            },
            {
                "fieldname": "trackflow_medium",
                "label": "Medium",
                "fieldtype": "Data",
                "insert_after": "trackflow_source"
            },
            {
                "fieldname": "trackflow_campaign",
                "label": "Campaign",
                "fieldtype": "Link",
                "options": "Campaign",
                "insert_after": "trackflow_medium"
            },
            {
                "fieldname": "trackflow_first_touch_date",
                "label": "First Touch Date",
                "fieldtype": "Datetime",
                "insert_after": "trackflow_campaign",
                "read_only": 1
            },
            {
                "fieldname": "trackflow_last_touch_date",
                "label": "Last Touch Date",
                "fieldtype": "Datetime",
                "insert_after": "trackflow_first_touch_date",
                "read_only": 1
            },
            {
                "fieldname": "trackflow_touch_count",
                "label": "Touch Count",
                "fieldtype": "Int",
                "insert_after": "trackflow_last_touch_date",
                "read_only": 1
            }
        ],
        "CRM Organization": [
            {
                "fieldname": "trackflow_visitor_id",
                "label": "TrackFlow Visitor ID",
                "fieldtype": "Data",
                "insert_after": "website",
                "read_only": 1
            },
            {
                "fieldname": "trackflow_engagement_score",
                "label": "Engagement Score",
                "fieldtype": "Int",
                "insert_after": "trackflow_visitor_id",
                "read_only": 1
            },
            {
                "fieldname": "trackflow_last_campaign",
                "label": "Last Campaign",
                "fieldtype": "Link",
                "options": "Campaign",
                "insert_after": "trackflow_engagement_score"
            }
        ],
        "CRM Deal": [
            {
                "fieldname": "trackflow_attribution_model",
                "label": "Attribution Model",
                "fieldtype": "Select",
                "options": "Last Touch\nFirst Touch\nLinear\nTime Decay\nPosition Based",
                "insert_after": "annual_revenue",
                "default": "Last Touch"
            },
            {
                "fieldname": "trackflow_first_touch_source",
                "label": "First Touch Source",
                "fieldtype": "Data",
                "insert_after": "trackflow_attribution_model",
                "read_only": 1
            },
            {
                "fieldname": "trackflow_last_touch_source",
                "label": "Last Touch Source",
                "fieldtype": "Data",
                "insert_after": "trackflow_first_touch_source",
                "read_only": 1
            },
            {
                "fieldname": "trackflow_marketing_influenced",
                "label": "Marketing Influenced",
                "fieldtype": "Check",
                "insert_after": "trackflow_last_touch_source",
                "read_only": 1
            },
            {
                "fieldname": "trackflow_attribution_data",
                "label": "Attribution Data",
                "fieldtype": "Long Text",
                "insert_after": "trackflow_marketing_influenced",
                "read_only": 1,
                "hidden": 1
            }
        ]
    }
    
    for doctype, fields in custom_fields.items():
        if frappe.db.exists("DocType", doctype):
            for field in fields:
                field_name = f"{doctype}-{field['fieldname']}"
                if not frappe.db.exists("Custom Field", field_name):
                    cf = frappe.new_doc("Custom Field")
                    cf.dt = doctype
                    cf.update(field)
                    cf.insert()
                    print(f"Created custom field: {field_name}")

def create_fcrm_property_setters():
    """Create property setters for FCRM DocTypes"""
    property_setters = [
        {
            "doc_type": "CRM Lead",
            "doctype_or_field": "DocType",
            "property": "track_changes",
            "value": "1",
            "property_type": "Check"
        },
        {
            "doc_type": "CRM Deal",
            "doctype_or_field": "DocType",
            "property": "track_changes",
            "value": "1",
            "property_type": "Check"
        },
        {
            "doc_type": "CRM Organization",
            "doctype_or_field": "DocType",
            "property": "track_changes",
            "value": "1",
            "property_type": "Check"
        }
    ]
    
    for ps in property_setters:
        ps_name = f"{ps['doc_type']}-main-{ps['property']}"
        if not frappe.db.exists("Property Setter", ps_name):
            prop_setter = frappe.new_doc("Property Setter")
            prop_setter.doc_type = ps['doc_type']
            prop_setter.doctype_or_field = ps['doctype_or_field']
            prop_setter.property = ps['property']
            prop_setter.value = ps['value']
            prop_setter.property_type = ps['property_type']
            prop_setter.insert()
            print(f"Created property setter: {ps_name}")

def create_default_data():
    """Create default data for TrackFlow"""
    # Create default attribution models
    attribution_models = [
        {"name": "Last Touch", "description": "100% credit to the last touchpoint"},
        {"name": "First Touch", "description": "100% credit to the first touchpoint"},
        {"name": "Linear", "description": "Equal credit to all touchpoints"},
        {"name": "Time Decay", "description": "More credit to recent touchpoints"},
        {"name": "Position Based", "description": "40% first, 40% last, 20% middle"}
    ]
    
    # Create default campaign types
    campaign_types = [
        {"name": "Email Marketing", "description": "Email campaigns and newsletters"},
        {"name": "Social Media", "description": "Social media marketing campaigns"},
        {"name": "Search Marketing", "description": "SEM and SEO campaigns"},
        {"name": "Content Marketing", "description": "Blog posts and content campaigns"},
        {"name": "Event Marketing", "description": "Webinars, trade shows, and events"},
        {"name": "Partner Marketing", "description": "Partner and affiliate campaigns"}
    ]
    
    # Create sample UTM sources
    utm_sources = [
        {"source": "google", "description": "Google search and ads"},
        {"source": "facebook", "description": "Facebook ads and posts"},
        {"source": "linkedin", "description": "LinkedIn ads and posts"},
        {"source": "twitter", "description": "Twitter ads and posts"},
        {"source": "email", "description": "Email campaigns"},
        {"source": "newsletter", "description": "Newsletter campaigns"},
        {"source": "partner", "description": "Partner referrals"}
    ]
    
    # Create sample UTM mediums
    utm_mediums = [
        {"medium": "cpc", "description": "Cost per click"},
        {"medium": "organic", "description": "Organic search"},
        {"medium": "social", "description": "Social media"},
        {"medium": "email", "description": "Email"},
        {"medium": "referral", "description": "Referral"},
        {"medium": "banner", "description": "Display advertising"},
        {"medium": "affiliate", "description": "Affiliate marketing"}
    ]
    
    print("Default data created successfully")

def setup_permissions():
    """Set up permissions for TrackFlow doctypes"""
    permissions = {
        "Campaign": [
            {"role": "TrackFlow Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "submit": 1, "cancel": 1},
            {"role": "TrackFlow User", "read": 1, "write": 1, "create": 1, "delete": 0, "submit": 0, "cancel": 0},
            {"role": "Sales User", "read": 1, "write": 0, "create": 0, "delete": 0}
        ],
        "Tracking Link": [
            {"role": "TrackFlow Manager", "read": 1, "write": 1, "create": 1, "delete": 1},
            {"role": "TrackFlow User", "read": 1, "write": 1, "create": 1, "delete": 0},
            {"role": "Sales User", "read": 1, "write": 0, "create": 0, "delete": 0}
        ],
        "Visitor": [
            {"role": "TrackFlow Manager", "read": 1, "write": 1, "create": 1, "delete": 1},
            {"role": "TrackFlow User", "read": 1, "write": 0, "create": 0, "delete": 0},
            {"role": "Sales User", "read": 1, "write": 0, "create": 0, "delete": 0}
        ],
        "Visitor Event": [
            {"role": "TrackFlow Manager", "read": 1, "write": 1, "create": 1, "delete": 1},
            {"role": "TrackFlow User", "read": 1, "write": 0, "create": 0, "delete": 0},
            {"role": "Sales User", "read": 1, "write": 0, "create": 0, "delete": 0}
        ]
    }
    
    for doctype, perms in permissions.items():
        if frappe.db.exists("DocType", doctype):
            for perm in perms:
                if not frappe.db.exists("DocPerm", {"parent": doctype, "role": perm["role"]}):
                    doc_perm = frappe.new_doc("DocPerm")
                    doc_perm.parent = doctype
                    doc_perm.parenttype = "DocType"
                    doc_perm.parentfield = "permissions"
                    doc_perm.update(perm)
                    doc_perm.insert()
                    print(f"Created permission for {perm['role']} in {doctype}")

def create_workspace():
    """Create TrackFlow workspace"""
    if not frappe.db.exists("Workspace", "TrackFlow"):
        workspace = frappe.new_doc("Workspace")
        workspace.name = "TrackFlow"
        workspace.label = "TrackFlow"
        workspace.icon = "fa fa-link"
        workspace.color = "#2563eb"
        workspace.module = "TrackFlow"
        workspace.category = "Modules"
        workspace.is_standard = 1
        workspace.public = 1
        workspace.content = get_workspace_content()
        workspace.insert()
        print("Created TrackFlow workspace")

def update_workspace():
    """Update workspace if it exists"""
    if frappe.db.exists("Workspace", "TrackFlow"):
        workspace = frappe.get_doc("Workspace", "TrackFlow")
        workspace.content = get_workspace_content()
        workspace.save()
        print("Updated TrackFlow workspace")

def get_workspace_content():
    """Get workspace content JSON"""
    return """[
        {
            "type": "header",
            "data": {
                "text": "TrackFlow Analytics",
                "level": 4
            }
        },
        {
            "type": "card",
            "data": {
                "card_name": "Dashboard",
                "col": 4
            }
        },
        {
            "type": "card",
            "data": {
                "card_name": "Campaigns",
                "col": 4
            }
        },
        {
            "type": "card",
            "data": {
                "card_name": "Links",
                "col": 4
            }
        },
        {
            "type": "card",
            "data": {
                "card_name": "Analytics",
                "col": 4
            }
        },
        {
            "type": "card",
            "data": {
                "card_name": "Reports",
                "col": 4
            }
        },
        {
            "type": "card",
            "data": {
                "card_name": "Settings",
                "col": 4
            }
        }
    ]"""

def enable_tracking():
    """Enable tracking for the site"""
    # Enable tracking in website settings
    website_settings = frappe.get_single("Website Settings")
    
    # Add tracking script to header
    if not website_settings.head_html:
        website_settings.head_html = ""
    
    tracking_script = """<!-- TrackFlow Analytics -->
<script src="/api/method/trackflow.api.tracking.get_tracking_script" async></script>
<!-- End TrackFlow Analytics -->"""
    
    if tracking_script not in website_settings.head_html:
        website_settings.head_html += "\n" + tracking_script
        website_settings.save()
        print("Added TrackFlow tracking script to website")
