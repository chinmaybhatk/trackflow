"""
Emergency diagnostic script for TrackFlow
"""

import frappe

@frappe.whitelist(allow_guest=True)
def diagnose():
    """Emergency diagnostic endpoint that bypasses all hooks"""
    try:
        # Basic system check
        result = {
            "status": "checking",
            "app_installed": "trackflow" in frappe.get_installed_apps(),
            "errors": []
        }
        
        # Check if TrackFlow Settings exists
        try:
            settings_exists = frappe.db.exists("TrackFlow Settings", "TrackFlow Settings")
            result["settings_exists"] = settings_exists
            
            if settings_exists:
                # Try to get the settings document
                settings = frappe.get_doc("TrackFlow Settings", "TrackFlow Settings")
                result["settings_accessible"] = True
                result["tracking_enabled"] = settings.enable_tracking
            else:
                result["settings_accessible"] = False
                result["tracking_enabled"] = False
                
        except Exception as e:
            result["errors"].append(f"Settings error: {str(e)}")
            result["settings_accessible"] = False
        
        # Check workspace
        try:
            workspace_exists = frappe.db.exists("Workspace", "TrackFlow")
            result["workspace_exists"] = workspace_exists
        except Exception as e:
            result["errors"].append(f"Workspace error: {str(e)}")
            result["workspace_exists"] = False
        
        # Check for common DocType issues
        doctypes_to_check = [
            "Tracked Link",
            "Link Campaign", 
            "Click Event",
            "Attribution Model",
            "TrackFlow Settings"
        ]
        
        result["doctypes"] = {}
        for dt in doctypes_to_check:
            try:
                exists = frappe.db.exists("DocType", dt)
                result["doctypes"][dt] = exists
            except Exception as e:
                result["doctypes"][dt] = f"Error: {str(e)}"
        
        # Check if hooks are causing issues
        try:
            hooks = frappe.get_hooks()
            trackflow_hooks = {
                "before_request": hooks.get("before_request", []),
                "after_request": hooks.get("after_request", [])
            }
            result["hooks"] = trackflow_hooks
        except Exception as e:
            result["errors"].append(f"Hooks error: {str(e)}")
        
        result["status"] = "completed"
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "type": type(e).__name__
        }
