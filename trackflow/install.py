import frappe
from frappe import _


def before_install():
    """Tasks to run before installing TrackFlow"""
    check_dependencies()
    create_roles()


def after_install():
    """Tasks to run after installing TrackFlow"""
    create_fcrm_custom_fields()
    create_fcrm_property_setters()
    create_trackflow_settings()
    setup_permissions()


def after_migrate():
    """Tasks to run after migration"""
    create_fcrm_custom_fields()
    create_trackflow_settings()


def check_dependencies():
    """Check if required apps are installed"""
    installed_apps = frappe.get_installed_apps()

    if "crm" not in installed_apps:
        frappe.throw(_("TrackFlow requires Frappe CRM to be installed"))


def create_trackflow_settings():
    """Create TrackFlow Settings with default values"""
    if frappe.db.exists("TrackFlow Settings", "TrackFlow Settings"):
        return

    try:
        settings = frappe.new_doc("TrackFlow Settings")
        settings.update(
            {
                "enable_tracking": 1,
                "auto_generate_short_codes": 1,
                "short_code_length": 6,
                "exclude_internal_traffic": 0,
                "gdpr_compliance_enabled": 1,
                "cookie_expires_days": 365,
                "default_attribution_model": "Last Touch",
                "attribution_window_days": 30,
                "cookie_consent_required": 1,
                "cookie_consent_text": "This site uses cookies for analytics and personalization.",
                "anonymize_ip_addresses": 0,
            }
        )

        default_ranges = [
            {"ip_range": "127.0.0.0/8", "description": "Localhost"},
            {"ip_range": "10.0.0.0/8", "description": "Private Class A"},
            {"ip_range": "172.16.0.0/12", "description": "Private Class B"},
            {"ip_range": "192.168.0.0/16", "description": "Private Class C"},
        ]

        for ip_range in default_ranges:
            settings.append("internal_ip_ranges", ip_range)

        settings.insert(ignore_permissions=True)
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(f"Error creating TrackFlow Settings: {str(e)}", "TrackFlow Install")


def create_roles():
    """Create roles required for TrackFlow"""
    roles = [
        {"role_name": "TrackFlow Manager", "desk_access": 1},
        {"role_name": "TrackFlow User", "desk_access": 1},
    ]

    for role_data in roles:
        if not frappe.db.exists("Role", role_data["role_name"]):
            role = frappe.new_doc("Role")
            role.update(role_data)
            role.insert(ignore_permissions=True)


def create_fcrm_custom_fields():
    """Create custom fields for FCRM DocTypes"""
    custom_fields = {
        "CRM Lead": [
            {
                "fieldname": "trackflow_tab",
                "label": "TrackFlow",
                "fieldtype": "Tab Break",
                "insert_after": "notes_tab",
            },
            {
                "fieldname": "trackflow_visitor_id",
                "label": "TrackFlow Visitor ID",
                "fieldtype": "Data",
                "insert_after": "trackflow_tab",
                "read_only": 1,
            },
            {
                "fieldname": "trackflow_source",
                "label": "Source",
                "fieldtype": "Data",
                "insert_after": "trackflow_visitor_id",
            },
            {
                "fieldname": "trackflow_medium",
                "label": "Medium",
                "fieldtype": "Data",
                "insert_after": "trackflow_source",
            },
            {
                "fieldname": "trackflow_campaign",
                "label": "Campaign",
                "fieldtype": "Link",
                "options": "Link Campaign",
                "insert_after": "trackflow_medium",
            },
            {
                "fieldname": "trackflow_first_touch_date",
                "label": "First Touch Date",
                "fieldtype": "Datetime",
                "insert_after": "trackflow_campaign",
                "read_only": 1,
            },
            {
                "fieldname": "trackflow_last_touch_date",
                "label": "Last Touch Date",
                "fieldtype": "Datetime",
                "insert_after": "trackflow_first_touch_date",
                "read_only": 1,
            },
            {
                "fieldname": "trackflow_touch_count",
                "label": "Touch Count",
                "fieldtype": "Int",
                "insert_after": "trackflow_last_touch_date",
                "read_only": 1,
            },
        ],
        "CRM Organization": [
            {
                "fieldname": "trackflow_tab",
                "label": "TrackFlow",
                "fieldtype": "Tab Break",
                "insert_after": "notes",
            },
            {
                "fieldname": "trackflow_visitor_id",
                "label": "TrackFlow Visitor ID",
                "fieldtype": "Data",
                "insert_after": "trackflow_tab",
                "read_only": 1,
            },
            {
                "fieldname": "trackflow_engagement_score",
                "label": "Engagement Score",
                "fieldtype": "Int",
                "insert_after": "trackflow_visitor_id",
                "read_only": 1,
            },
            {
                "fieldname": "trackflow_last_campaign",
                "label": "Last Campaign",
                "fieldtype": "Link",
                "options": "Link Campaign",
                "insert_after": "trackflow_engagement_score",
            },
        ],
        "CRM Deal": [
            {
                "fieldname": "trackflow_tab",
                "label": "TrackFlow Attribution",
                "fieldtype": "Tab Break",
                "insert_after": "contact_tab",
            },
            {
                "fieldname": "trackflow_attribution_model",
                "label": "Attribution Model",
                "fieldtype": "Select",
                "options": "Last Touch\nFirst Touch\nLinear\nTime Decay\nPosition Based",
                "insert_after": "trackflow_tab",
                "default": "Last Touch",
            },
            {
                "fieldname": "trackflow_first_touch_source",
                "label": "First Touch Source",
                "fieldtype": "Data",
                "insert_after": "trackflow_attribution_model",
                "read_only": 1,
            },
            {
                "fieldname": "trackflow_last_touch_source",
                "label": "Last Touch Source",
                "fieldtype": "Data",
                "insert_after": "trackflow_first_touch_source",
                "read_only": 1,
            },
            {
                "fieldname": "trackflow_marketing_influenced",
                "label": "Marketing Influenced",
                "fieldtype": "Check",
                "insert_after": "trackflow_last_touch_source",
                "read_only": 1,
            },
        ],
        "Web Form": [
            {
                "fieldname": "trackflow_section",
                "label": "TrackFlow Settings",
                "fieldtype": "Section Break",
                "insert_after": "custom_css",
            },
            {
                "fieldname": "trackflow_tracking_enabled",
                "label": "Enable TrackFlow Tracking",
                "fieldtype": "Check",
                "insert_after": "trackflow_section",
            },
            {
                "fieldname": "trackflow_conversion_goal",
                "label": "Conversion Goal",
                "fieldtype": "Link",
                "options": "Link Campaign",
                "insert_after": "trackflow_tracking_enabled",
                "depends_on": "trackflow_tracking_enabled",
            },
        ],
    }

    for doctype, fields in custom_fields.items():
        if not frappe.db.exists("DocType", doctype):
            continue
        for field in fields:
            field_name = f"{doctype}-{field['fieldname']}"
            if not frappe.db.exists("Custom Field", field_name):
                cf = frappe.new_doc("Custom Field")
                cf.dt = doctype
                cf.update(field)
                try:
                    cf.insert(ignore_permissions=True)
                except Exception:
                    pass


def create_fcrm_property_setters():
    """Create property setters for FCRM DocTypes"""
    property_setters = [
        {
            "doc_type": "CRM Lead",
            "doctype_or_field": "DocType",
            "property": "track_changes",
            "value": "1",
            "property_type": "Check",
        },
        {
            "doc_type": "CRM Deal",
            "doctype_or_field": "DocType",
            "property": "track_changes",
            "value": "1",
            "property_type": "Check",
        },
        {
            "doc_type": "CRM Organization",
            "doctype_or_field": "DocType",
            "property": "track_changes",
            "value": "1",
            "property_type": "Check",
        },
    ]

    for ps in property_setters:
        ps_name = f"{ps['doc_type']}-main-{ps['property']}"
        if not frappe.db.exists("Property Setter", ps_name):
            try:
                prop_setter = frappe.new_doc("Property Setter")
                prop_setter.doc_type = ps["doc_type"]
                prop_setter.doctype_or_field = ps["doctype_or_field"]
                prop_setter.property = ps["property"]
                prop_setter.value = ps["value"]
                prop_setter.property_type = ps["property_type"]
                prop_setter.insert(ignore_permissions=True)
            except Exception:
                pass


def setup_permissions():
    """Set up permissions for TrackFlow doctypes"""
    trackflow_doctypes = [
        "Link Campaign",
        "Tracked Link",
        "Click Event",
        "Attribution Model",
        "TrackFlow Settings",
        "Visitor",
        "Visitor Event",
        "Visitor Session",
        "Conversion",
    ]

    for doctype in trackflow_doctypes:
        if not frappe.db.exists("DocType", doctype):
            continue
        if frappe.db.exists("DocPerm", {"parent": doctype, "role": "TrackFlow Manager"}):
            continue

        try:
            meta = frappe.get_meta(doctype)
            doc_perm = frappe.new_doc("DocPerm")
            doc_perm.parent = doctype
            doc_perm.parenttype = "DocType"
            doc_perm.parentfield = "permissions"
            doc_perm.role = "TrackFlow Manager"
            doc_perm.read = 1
            doc_perm.write = 1
            doc_perm.create = 1
            doc_perm.delete = 1
            doc_perm.submit = 1 if meta.is_submittable else 0
            doc_perm.cancel = 1 if meta.is_submittable else 0
            doc_perm.insert(ignore_permissions=True)
        except Exception:
            pass
