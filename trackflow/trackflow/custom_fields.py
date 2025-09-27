import frappe

def create_custom_fields():
    """Create custom fields for TrackFlow integration"""
    
    custom_fields = {
        "Lead": [
            {
                "fieldname": "trackflow_section",
                "label": "TrackFlow Analytics",
                "fieldtype": "Section Break",
                "insert_after": "contact_by",
                "collapsible": 1
            },
            {
                "fieldname": "trackflow_visitor_id",
                "label": "Visitor ID",
                "fieldtype": "Data",
                "insert_after": "trackflow_section",
                "read_only": 1,
                "no_copy": 1
            },
            {
                "fieldname": "trackflow_source",
                "label": "First Touch Source",
                "fieldtype": "Data",
                "insert_after": "trackflow_visitor_id",
                "read_only": 1
            },
            {
                "fieldname": "trackflow_medium",
                "label": "First Touch Medium",
                "fieldtype": "Data",
                "insert_after": "trackflow_source",
                "read_only": 1
            },
            {
                "fieldname": "trackflow_column_break_1",
                "fieldtype": "Column Break",
                "insert_after": "trackflow_medium"
            },
            {
                "fieldname": "trackflow_campaign",
                "label": "First Touch Campaign",
                "fieldtype": "Link",
                "options": "Link Campaign",
                "insert_after": "trackflow_column_break_1",
                "read_only": 1
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
                "label": "Total Touchpoints",
                "fieldtype": "Int",
                "insert_after": "trackflow_last_touch_date",
                "read_only": 1,
                "default": 0
            }
        ],
        "Contact": [
            {
                "fieldname": "trackflow_section",
                "label": "TrackFlow Analytics",
                "fieldtype": "Section Break",
                "insert_after": "is_primary_contact",
                "collapsible": 1
            },
            {
                "fieldname": "trackflow_visitor_id",
                "label": "Visitor ID",
                "fieldtype": "Data",
                "insert_after": "trackflow_section",
                "read_only": 1,
                "no_copy": 1
            },
            {
                "fieldname": "trackflow_engagement_score",
                "label": "Engagement Score",
                "fieldtype": "Int",
                "insert_after": "trackflow_visitor_id",
                "read_only": 1,
                "default": 0
            },
            {
                "fieldname": "trackflow_last_campaign",
                "label": "Last Campaign",
                "fieldtype": "Link",
                "options": "Link Campaign",
                "insert_after": "trackflow_engagement_score",
                "read_only": 1
            }
        ],
        "Opportunity": [
            {
                "fieldname": "trackflow_section",
                "label": "TrackFlow Attribution",
                "fieldtype": "Section Break",
                "insert_after": "contact_email",
                "collapsible": 1
            },
            {
                "fieldname": "trackflow_campaign",
                "label": "Primary Campaign",
                "fieldtype": "Link",
                "options": "Link Campaign",
                "insert_after": "trackflow_section"
            },
            {
                "fieldname": "trackflow_source",
                "label": "Lead Source",
                "fieldtype": "Data",
                "insert_after": "trackflow_campaign",
                "read_only": 1
            },
            {
                "fieldname": "trackflow_attribution_model",
                "label": "Attribution Model",
                "fieldtype": "Select",
                "options": "\nLast Touch\nFirst Touch\nLinear\nTime Decay\nPosition Based",
                "insert_after": "trackflow_source",
                "default": "Last Touch"
            },
            {
                "fieldname": "trackflow_column_break_2",
                "fieldtype": "Column Break",
                "insert_after": "trackflow_attribution_model"
            },
            {
                "fieldname": "trackflow_first_touch_source",
                "label": "First Touch Source",
                "fieldtype": "Data",
                "insert_after": "trackflow_column_break_2",
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
            }
        ],
        "Web Form": [
            {
                "fieldname": "trackflow_section",
                "label": "TrackFlow Settings",
                "fieldtype": "Section Break",
                "insert_after": "published",
                "collapsible": 1
            },
            {
                "fieldname": "trackflow_tracking_enabled",
                "label": "Enable TrackFlow Tracking",
                "fieldtype": "Check",
                "insert_after": "trackflow_section",
                "default": 1
            },
            {
                "fieldname": "trackflow_conversion_goal",
                "label": "Conversion Goal",
                "fieldtype": "Link",
                "options": "Campaign Goal",
                "insert_after": "trackflow_tracking_enabled",
                "description": "Link form submission to a campaign goal"
            }
        ],
        "Customer": [
            {
                "fieldname": "trackflow_section",
                "label": "TrackFlow Analytics",
                "fieldtype": "Section Break",
                "insert_after": "represents_company",
                "collapsible": 1
            },
            {
                "fieldname": "trackflow_acquisition_campaign",
                "label": "Acquisition Campaign",
                "fieldtype": "Link",
                "options": "Link Campaign",
                "insert_after": "trackflow_section",
                "read_only": 1
            },
            {
                "fieldname": "trackflow_acquisition_source",
                "label": "Acquisition Source",
                "fieldtype": "Data",
                "insert_after": "trackflow_acquisition_campaign",
                "read_only": 1
            },
            {
                "fieldname": "trackflow_lifetime_value",
                "label": "Customer Lifetime Value",
                "fieldtype": "Currency",
                "insert_after": "trackflow_acquisition_source",
                "read_only": 1
            }
        ]
    }
    
    for doctype, fields in custom_fields.items():
        for field in fields:
            if not frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": field["fieldname"]}):
                cf = frappe.new_doc("Custom Field")
                cf.dt = doctype
                cf.update(field)
                cf.insert()
                print(f"Created custom field {field['fieldname']} in {doctype}")

def create_property_setters():
    """Create property setters for TrackFlow"""
    property_setters = [
        {
            "doctype": "Lead",
            "property": "track_views",
            "value": "1",
            "property_type": "Check"
        },
        {
            "doctype": "Opportunity",
            "property": "track_views", 
            "value": "1",
            "property_type": "Check"
        },
        {
            "doctype": "Web Form",
            "property": "allow_guest",
            "value": "1",
            "property_type": "Check"
        }
    ]
    
    for ps in property_setters:
        if not frappe.db.exists("Property Setter", {
            "doc_type": ps["doctype"],
            "property": ps["property"]
        }):
            prop_setter = frappe.new_doc("Property Setter")
            prop_setter.doctype_or_field = "DocType"
            prop_setter.doc_type = ps["doctype"]
            prop_setter.property = ps["property"]
            prop_setter.value = ps["value"]
            prop_setter.property_type = ps["property_type"]
            prop_setter.insert()
            print(f"Created property setter for {ps['doctype']}.{ps['property']}")

def remove_custom_fields():
    """Remove custom fields created by TrackFlow"""
    doctypes = ["Lead", "Contact", "Opportunity", "Web Form", "Customer"]
    
    for doctype in doctypes:
        custom_fields = frappe.get_all(
            "Custom Field",
            filters={
                "dt": doctype,
                "fieldname": ["like", "trackflow_%"]
            },
            fields=["name"]
        )
        
        for cf in custom_fields:
            frappe.delete_doc("Custom Field", cf.name)
            print(f"Removed custom field {cf.name}")
