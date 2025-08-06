import frappe

@frappe.whitelist(allow_guest=True)
def test():
    """Test endpoint to verify TrackFlow is working"""
    return {
        "success": True,
        "message": "TrackFlow is installed and working!",
        "app_version": "1.0.0"
    }

@frappe.whitelist(allow_guest=True)
def debug():
    """Debug endpoint to check app status"""
    try:
        # Check if TrackFlow Settings exists and can be accessed
        settings_exists = False
        settings_accessible = False
        try:
            settings = frappe.get_doc("TrackFlow Settings", "TrackFlow Settings")
            settings_exists = True
            settings_accessible = True
        except:
            settings_exists = frappe.db.exists("DocType", "TrackFlow Settings")
        
        # Check if key doctypes exist
        doctypes_check = {
            "Link Campaign": frappe.db.exists("DocType", "Link Campaign"),
            "Tracked Link": frappe.db.exists("DocType", "Tracked Link"),
            "Click Event": frappe.db.exists("DocType", "Click Event"),
            "Attribution Model": frappe.db.exists("DocType", "Attribution Model"),
            "TrackFlow Settings": settings_exists
        }
        
        # Check for expected but missing doctypes
        missing_expected = {
            "Campaign": frappe.db.exists("DocType", "Campaign"),
            "Tracking Link": frappe.db.exists("DocType", "Tracking Link"),
            "Visitor": frappe.db.exists("DocType", "Visitor"),
            "Visitor Event": frappe.db.exists("DocType", "Visitor Event"),
            "Visitor Session": frappe.db.exists("DocType", "Visitor Session"),
            "Conversion": frappe.db.exists("DocType", "Conversion")
        }
        
        # Check if workspace exists
        workspace_exists = frappe.db.exists("Workspace", "TrackFlow")
        
        return {
            "success": True,
            "settings_exists": settings_exists,
            "settings_accessible": settings_accessible,
            "existing_doctypes": doctypes_check,
            "expected_but_missing": missing_expected,
            "workspace_exists": workspace_exists,
            "summary": {
                "actual_doctypes_exist": all(doctypes_check.values()),
                "expected_doctypes_missing": not any(missing_expected.values()),
                "ready_to_use": all(doctypes_check.values()) and workspace_exists
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
