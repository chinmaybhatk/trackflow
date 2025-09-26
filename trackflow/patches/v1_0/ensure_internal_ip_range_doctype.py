import frappe
from frappe.modules.import_file import import_file_by_path
import os

def execute():
    """Ensure Internal IP Range DocType is properly created"""
    
    try:
        # Check if DocType already exists
        if frappe.db.exists("DocType", "Internal IP Range"):
            print("Internal IP Range DocType already exists")
            return
            
        # Import the DocType from JSON file
        app_path = frappe.get_app_path("trackflow")
        doctype_path = os.path.join(
            app_path, "trackflow", "doctype", "internal_ip_range", "internal_ip_range.json"
        )
        
        if os.path.exists(doctype_path):
            # Import the DocType
            import_file_by_path(doctype_path, force=True)
            frappe.db.commit()
            print("✓ Successfully created Internal IP Range DocType")
        else:
            # Create manually if JSON file doesn't exist
            create_internal_ip_range_doctype()
            
    except Exception as e:
        frappe.log_error(f"Error creating Internal IP Range DocType: {str(e)}", "TrackFlow Patch")
        print(f"Error creating Internal IP Range DocType: {str(e)}")
        # Try creating manually as fallback
        create_internal_ip_range_doctype()

def create_internal_ip_range_doctype():
    """Create Internal IP Range DocType manually"""
    
    try:
        # Create the DocType document
        doctype_doc = frappe.new_doc("DocType")
        doctype_doc.update({
            "name": "Internal IP Range",
            "module": "TrackFlow", 
            "istable": 1,
            "engine": "InnoDB",
            "allow_rename": 0,
            "index_web_pages_for_search": 1,
            "sort_field": "modified",
            "sort_order": "DESC"
        })
        
        # Add fields
        fields = [
            {
                "fieldname": "ip_range",
                "fieldtype": "Data",
                "label": "IP Range",
                "reqd": 1,
                "in_list_view": 1
            },
            {
                "fieldname": "description", 
                "fieldtype": "Data",
                "label": "Description",
                "in_list_view": 1
            }
        ]
        
        for field in fields:
            doctype_doc.append("fields", field)
            
        # Insert the DocType
        doctype_doc.insert()
        frappe.db.commit()
        
        print("✓ Manually created Internal IP Range DocType")
        
    except Exception as e:
        frappe.log_error(f"Error manually creating Internal IP Range: {str(e)}", "TrackFlow Patch")
        print(f"Failed to create Internal IP Range DocType: {str(e)}")
        raise