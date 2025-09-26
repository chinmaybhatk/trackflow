import frappe
from frappe import _

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
    
    # Enable tracking
    enable_tracking()
    
    print("TrackFlow installation completed!")
    frappe.msgprint(_("TrackFlow has been successfully installed!"), indicator="green")

def after_migrate():
    """Tasks to run after migration"""
    # Update custom fields if needed
    create_fcrm_custom_fields()

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
                "fieldname": "trackflow_tab",
                "label": "TrackFlow",
                "fieldtype": "Tab Break",
                "insert_after": "notes_tab"
            },
            {
                "fieldname": "trackflow_visitor_id",
                "label": "TrackFlow Visitor ID",
                "fieldtype": "Data",
                "insert_after": "trackflow_tab",
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
                "options": "Link Campaign",
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
                "fieldname": "trackflow_tab",
                "label": "TrackFlow",
                "fieldtype": "Tab Break",
                "insert_after": "notes"
            },
            {
                "fieldname": "trackflow_visitor_id",
                "label": "TrackFlow Visitor ID",
                "fieldtype": "Data",
                "insert_after": "trackflow_tab",
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
                "options": "Link Campaign",
                "insert_after": "trackflow_engagement_score"
            }
        ],
        "CRM Deal": [
            {
                "fieldname": "trackflow_tab",
                "label": "TrackFlow Attribution",
                "fieldtype": "Tab Break",
                "insert_after": "contact_tab"
            },
            {
                "fieldname": "trackflow_attribution_model",
                "label": "Attribution Model",
                "fieldtype": "Select",
                "options": "Last Touch\nFirst Touch\nLinear\nTime Decay\nPosition Based",
                "insert_after": "trackflow_tab",
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
        ],
        "Web Form": [
            {
                "fieldname": "trackflow_section",
                "label": "TrackFlow Settings",
                "fieldtype": "Section Break",
                "insert_after": "custom_css"
            },
            {
                "fieldname": "trackflow_tracking_enabled",
                "label": "Enable TrackFlow Tracking",
                "fieldtype": "Check",
                "insert_after": "trackflow_section"
            },
            {
                "fieldname": "trackflow_conversion_goal",
                "label": "Conversion Goal",
                "fieldtype": "Link",
                "options": "Link Campaign",
                "insert_after": "trackflow_tracking_enabled",
                "depends_on": "trackflow_tracking_enabled"
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
    
    print("Default data created successfully")

def setup_permissions():
    """Set up permissions for TrackFlow doctypes"""
    # Only set permissions for DocTypes that actually exist
    existing_doctypes = []
    
    # Check which TrackFlow DocTypes exist
    possible_doctypes = [
        "Link Campaign", "Tracked Link", "Click Event", "Attribution Model",
        "TrackFlow Settings", "Campaign Goal", "Visitor", "Visitor Event"
    ]
    
    for dt in possible_doctypes:
        if frappe.db.exists("DocType", dt):
            existing_doctypes.append(dt)
    
    print(f"Found existing TrackFlow DocTypes: {existing_doctypes}")
    
    # Set permissions for existing DocTypes
    for doctype in existing_doctypes:
        # Skip if permissions already exist
        if frappe.db.exists("DocPerm", {"parent": doctype, "role": "TrackFlow Manager"}):
            continue
            
        # Add permissions for TrackFlow Manager
        doc_perm = frappe.new_doc("DocPerm")
        doc_perm.parent = doctype
        doc_perm.parenttype = "DocType"
        doc_perm.parentfield = "permissions"
        doc_perm.role = "TrackFlow Manager"
        doc_perm.read = 1
        doc_perm.write = 1
        doc_perm.create = 1
        doc_perm.delete = 1
        doc_perm.submit = 1 if frappe.get_meta(doctype).is_submittable else 0
        doc_perm.cancel = 1 if frappe.get_meta(doctype).is_submittable else 0
        doc_perm.insert()
        print(f"Created permission for TrackFlow Manager in {doctype}")

def enable_tracking():
    """Enable tracking for the site"""
    # Enable tracking in website settings
    try:
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
    except Exception as e:
        print(f"Could not add tracking script: {str(e)}")

def setup_crm_integration():
    """Set up CRM workspace integration"""
    try:
        # Check if CRM workspace exists
        if frappe.db.exists("Workspace", "CRM"):
            crm_workspace = frappe.get_doc("Workspace", "CRM")
            
            # Check if TrackFlow links already exist
            trackflow_exists = any(link.get('label') == 'TrackFlow Analytics' 
                                 for link in crm_workspace.links)
            
            if not trackflow_exists:
                # Add TrackFlow section to CRM workspace
                trackflow_links = [
                    {
                        "type": "Card Break",
                        "label": "TrackFlow Analytics",
                        "hidden": 0,
                        "onboard": 0
                    },
                    {
                        "type": "Link",
                        "link_type": "DocType",
                        "link_to": "Link Campaign", 
                        "label": "Campaigns",
                        "hidden": 0,
                        "onboard": 0
                    },
                    {
                        "type": "Link",
                        "link_type": "DocType",
                        "link_to": "Tracked Link",
                        "label": "Tracked Links", 
                        "hidden": 0,
                        "onboard": 0
                    },
                    {
                        "type": "Link",
                        "link_type": "DocType", 
                        "link_to": "Click Event",
                        "label": "Click Analytics",
                        "hidden": 0,
                        "onboard": 0
                    }
                ]
                
                # Append TrackFlow links to CRM workspace
                for link in trackflow_links:
                    crm_workspace.append("links", link)
                
                crm_workspace.save()
                frappe.db.commit()
                print("✓ TrackFlow integrated into CRM workspace")
                
    except Exception as e:
        frappe.log_error(f"Error setting up CRM integration: {str(e)}", "TrackFlow Install")
        print(f"Warning: Could not integrate with CRM workspace: {str(e)}")

def after_migrate():
    """Run after migration"""
    create_fcrm_custom_fields()
    create_default_data()
    setup_crm_integration()
    print("TrackFlow migration completed successfully!")
