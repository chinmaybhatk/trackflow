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
        # Check if TrackFlow Settings exists
        settings_exists = frappe.db.exists("DocType", "TrackFlow Settings")
        
        # Check if key doctypes exist
        doctypes = [
            "Campaign",
            "Tracking Link",
            "Visitor",
            "Visitor Event",
            "Visitor Session",
            "Conversion",
            "Attribution Model"
        ]
        
        missing_doctypes = []
        for dt in doctypes:
            if not frappe.db.exists("DocType", dt):
                missing_doctypes.append(dt)
        
        # Check if workspace exists
        workspace_exists = frappe.db.exists("Workspace", "TrackFlow")
        
        return {
            "success": True,
            "settings_exists": settings_exists,
            "missing_doctypes": missing_doctypes,
            "workspace_exists": workspace_exists,
            "all_good": len(missing_doctypes) == 0 and settings_exists and workspace_exists
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
