#!/usr/bin/env python3
"""
Manual script to create Internal IP Range DocType
Run this on Frappe console if the patch didn't work
"""

import frappe

def create_internal_ip_range_doctype():
    """Create Internal IP Range DocType manually"""
    
    # Check if DocType already exists
    if frappe.db.exists("DocType", "Internal IP Range"):
        print("✅ Internal IP Range DocType already exists")
        return
    
    print("🏗️ Creating Internal IP Range DocType...")
    
    # Create the DocType
    doctype = frappe.new_doc("DocType")
    doctype.update({
        "name": "Internal IP Range",
        "module": "TrackFlow",
        "istable": 1,  # Child table
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
            "in_list_view": 1,
            "description": "IP range in CIDR notation (e.g., 192.168.1.0/24)"
        },
        {
            "fieldname": "description",
            "fieldtype": "Data", 
            "label": "Description",
            "in_list_view": 1,
            "description": "Description of this IP range"
        }
    ]
    
    for field in fields:
        doctype.append("fields", field)
    
    # Insert the DocType
    doctype.insert(ignore_permissions=True)
    frappe.db.commit()
    
    print("✅ Internal IP Range DocType created successfully!")

def create_default_trackflow_settings():
    """Create TrackFlow Settings with default values"""
    
    # Check if settings already exist
    if frappe.db.exists("TrackFlow Settings", "TrackFlow Settings"):
        print("✅ TrackFlow Settings already exists")
        return
        
    print("🏗️ Creating TrackFlow Settings...")
    
    # Create settings
    settings = frappe.new_doc("TrackFlow Settings")
    settings.update({
        # General settings
        "enable_tracking": 1,
        "auto_generate_short_codes": 1,
        "short_code_length": 6,
        "exclude_internal_traffic": 0,
        "gdpr_compliance_enabled": 1,
        "cookie_expires_days": 365,
        
        # Attribution
        "default_attribution_model": "Last Touch",
        "attribution_window_days": 30,
        
        # Privacy
        "cookie_consent_required": 1,
        "cookie_consent_text": "This site uses cookies for analytics and personalization. By continuing to browse, you agree to our use of cookies.",
        "anonymize_ip_addresses": 0
    })
    
    # Add default IP ranges
    default_ranges = [
        {"ip_range": "127.0.0.0/8", "description": "Localhost"},
        {"ip_range": "10.0.0.0/8", "description": "Private Class A"},
        {"ip_range": "172.16.0.0/12", "description": "Private Class B"},
        {"ip_range": "192.168.0.0/16", "description": "Private Class C"}
    ]
    
    for ip_range in default_ranges:
        settings.append("internal_ip_ranges", ip_range)
    
    # Insert settings
    settings.insert(ignore_permissions=True)
    frappe.db.commit()
    
    print("✅ TrackFlow Settings created successfully!")

def fix_trackflow():
    """Complete fix for TrackFlow setup"""
    print("🚀 Starting TrackFlow setup fix...")
    
    try:
        # Step 1: Create Internal IP Range DocType
        create_internal_ip_range_doctype()
        
        # Step 2: Create TrackFlow Settings
        create_default_trackflow_settings()
        
        # Step 3: Clear cache
        frappe.clear_cache()
        
        print("🎉 TrackFlow setup completed successfully!")
        print("📍 You can now access TrackFlow Settings without errors")
        
    except Exception as e:
        print(f"❌ Error during setup: {str(e)}")
        frappe.log_error(f"TrackFlow setup error: {str(e)}", "TrackFlow Setup")

if __name__ == "__main__":
    fix_trackflow()

# Instructions for Frappe Console:
"""
To run this in Frappe console:

1. Go to your site console:
   bench --site [your-site] console

2. Run the following commands:
   
   import frappe
   
   # Create Internal IP Range DocType
   doctype = frappe.new_doc("DocType")
   doctype.update({
       "name": "Internal IP Range",
       "module": "TrackFlow",
       "istable": 1,
       "engine": "InnoDB"
   })
   
   # Add fields
   doctype.append("fields", {
       "fieldname": "ip_range",
       "fieldtype": "Data",
       "label": "IP Range",
       "reqd": 1,
       "in_list_view": 1
   })
   
   doctype.append("fields", {
       "fieldname": "description",
       "fieldtype": "Data",
       "label": "Description",
       "in_list_view": 1
   })
   
   # Save
   doctype.insert(ignore_permissions=True)
   frappe.db.commit()
   
   print("Internal IP Range DocType created!")

3. Then create TrackFlow Settings:
   
   settings = frappe.new_doc("TrackFlow Settings")
   settings.enable_tracking = 1
   settings.auto_generate_short_codes = 1
   settings.short_code_length = 6
   settings.default_attribution_model = "Last Touch"
   settings.attribution_window_days = 30
   settings.cookie_expires_days = 365
   settings.insert(ignore_permissions=True)
   frappe.db.commit()
   
   print("TrackFlow Settings created!")

4. Clear cache:
   frappe.clear_cache()
"""