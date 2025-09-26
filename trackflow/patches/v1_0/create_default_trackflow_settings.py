import frappe

def execute():
    """Create default TrackFlow Settings document"""
    
    try:
        # Check if TrackFlow Settings already exists
        if frappe.db.exists("TrackFlow Settings", "TrackFlow Settings"):
            print("TrackFlow Settings already exists")
            return
            
        # Check if Internal IP Range DocType exists
        if not frappe.db.exists("DocType", "Internal IP Range"):
            print("Internal IP Range DocType not found, skipping TrackFlow Settings creation")
            return
            
        # Create default TrackFlow Settings
        settings = frappe.new_doc("TrackFlow Settings")
        settings.update({
            # Core Settings
            "enable_tracking": 1,
            "auto_generate_short_codes": 1,
            "short_code_length": 6,
            "default_shortlink_domain": "",
            
            # Attribution
            "default_attribution_model": "Last Touch",
            "attribution_window_days": 30,
            
            # Privacy & Compliance
            "gdpr_compliance_enabled": 1,
            "cookie_consent_required": 1,
            "anonymize_ip_addresses": 0,
            "cookie_expires_days": 365,
            
            # Internal Traffic Filtering
            "exclude_internal_traffic": 0
        })
        
        # Add some common internal IP ranges
        common_ranges = [
            {"ip_range": "127.0.0.0/8", "description": "Localhost"},
            {"ip_range": "10.0.0.0/8", "description": "Private Class A"},
            {"ip_range": "172.16.0.0/12", "description": "Private Class B"},
            {"ip_range": "192.168.0.0/16", "description": "Private Class C"}
        ]
        
        for ip_range in common_ranges:
            settings.append("internal_ip_ranges", ip_range)
        
        # Insert the settings document
        settings.insert(ignore_permissions=True)
        frappe.db.commit()
        
        print("✓ Successfully created default TrackFlow Settings")
        print("✓ Added common internal IP ranges")
        
    except Exception as e:
        frappe.log_error(f"Error creating TrackFlow Settings: {str(e)}", "TrackFlow Patch")
        print(f"Error creating TrackFlow Settings: {str(e)}")
        
        # If creation fails, at least try to create empty settings
        try:
            empty_settings = frappe.new_doc("TrackFlow Settings")
            empty_settings.enable_tracking = 1
            empty_settings.insert(ignore_permissions=True)
            frappe.db.commit()
            print("✓ Created minimal TrackFlow Settings")
        except Exception as e2:
            print(f"Failed to create even minimal settings: {str(e2)}")