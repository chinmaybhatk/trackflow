"""
Debug API endpoints for TrackFlow
"""

import frappe
from frappe import _
import json
import traceback


@frappe.whitelist(allow_guest=True)
def test():
    """Simple test endpoint"""
    return {"success": True, "message": "TrackFlow API is working"}


@frappe.whitelist(allow_guest=True)
def debug():
    """Debug endpoint to check various aspects of the installation"""
    try:
        results = {
            "success": True,
            "checks": {}
        }
        
        # Check if app is installed
        results["checks"]["app_installed"] = {
            "status": "TrackFlow" in frappe.get_installed_apps(),
            "message": "TrackFlow app is installed"
        }
        
        # Check if workspace exists
        try:
            workspace_exists = frappe.db.exists("Workspace", "TrackFlow")
            results["checks"]["workspace"] = {
                "status": bool(workspace_exists),
                "message": f"TrackFlow workspace {'exists' if workspace_exists else 'does not exist'}"
            }
        except Exception as e:
            results["checks"]["workspace"] = {
                "status": False,
                "message": f"Error checking workspace: {str(e)}"
            }
        
        # Check key DocTypes
        doctypes_to_check = [
            "Tracked Link",
            "Link Campaign", 
            "Click Event",
            "TrackFlow Settings",
            "TrackFlow API Key"
        ]
        
        for doctype in doctypes_to_check:
            try:
                exists = frappe.db.table_exists(doctype.lower().replace(" ", "_"))
                results["checks"][f"doctype_{doctype}"] = {
                    "status": exists,
                    "message": f"{doctype} table {'exists' if exists else 'does not exist'}"
                }
            except Exception as e:
                results["checks"][f"doctype_{doctype}"] = {
                    "status": False,
                    "message": f"Error checking {doctype}: {str(e)}"
                }
        
        # Check permissions module
        try:
            from trackflow import permissions
            has_permission_func = hasattr(permissions, 'has_app_permission')
            results["checks"]["permissions_module"] = {
                "status": has_permission_func,
                "message": f"Permissions module {'has' if has_permission_func else 'missing'} has_app_permission function"
            }
        except Exception as e:
            results["checks"]["permissions_module"] = {
                "status": False,
                "message": f"Error loading permissions module: {str(e)}"
            }
        
        # Check if hooks are properly loaded
        try:
            hooks = frappe.get_hooks()
            has_after_request = "after_request" in hooks
            results["checks"]["hooks_loaded"] = {
                "status": has_after_request,
                "message": f"Hooks {'are' if has_after_request else 'are not'} properly loaded"
            }
        except Exception as e:
            results["checks"]["hooks_loaded"] = {
                "status": False,
                "message": f"Error checking hooks: {str(e)}"
            }
        
        # Check if there are any recent errors
        try:
            recent_errors = frappe.get_all(
                "Error Log",
                filters={
                    "creation": (">=", frappe.utils.add_days(frappe.utils.nowdate(), -1))
                },
                fields=["method", "error"],
                order_by="creation desc",
                limit=5
            )
            
            trackflow_errors = [
                err for err in recent_errors 
                if "trackflow" in (err.get("method", "") + err.get("error", "")).lower()
            ]
            
            results["checks"]["recent_errors"] = {
                "status": len(trackflow_errors) == 0,
                "message": f"Found {len(trackflow_errors)} TrackFlow-related errors in last 24 hours",
                "errors": trackflow_errors[:3] if trackflow_errors else []
            }
        except Exception as e:
            results["checks"]["recent_errors"] = {
                "status": False,
                "message": f"Error checking error logs: {str(e)}"
            }
        
        # Overall status
        all_checks_passed = all(check["status"] for check in results["checks"].values())
        results["overall_status"] = "All checks passed" if all_checks_passed else "Some checks failed"
        
        return results
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@frappe.whitelist(allow_guest=True)
def diagnose_error():
    """Diagnose the specific error causing Internal Server Error"""
    try:
        results = {
            "success": True,
            "diagnostics": {}
        }
        
        # Test database connection
        try:
            frappe.db.sql("SELECT 1")
            results["diagnostics"]["database"] = {
                "status": True,
                "message": "Database connection is working"
            }
        except Exception as e:
            results["diagnostics"]["database"] = {
                "status": False,
                "message": f"Database error: {str(e)}"
            }
        
        # Test session
        try:
            user = frappe.session.user if frappe.session else "No session"
            results["diagnostics"]["session"] = {
                "status": True,
                "message": f"Session is working, user: {user}"
            }
        except Exception as e:
            results["diagnostics"]["session"] = {
                "status": False,
                "message": f"Session error: {str(e)}"
            }
        
        # Test request object
        try:
            path = frappe.request.path if frappe.request else "No request"
            results["diagnostics"]["request"] = {
                "status": True,
                "message": f"Request object is available, path: {path}"
            }
        except Exception as e:
            results["diagnostics"]["request"] = {
                "status": False,
                "message": f"Request error: {str(e)}"
            }
        
        # Test TrackFlow settings access
        try:
            if frappe.db.exists("TrackFlow Settings", "TrackFlow Settings"):
                settings = frappe.get_doc("TrackFlow Settings", "TrackFlow Settings")
                results["diagnostics"]["settings"] = {
                    "status": True,
                    "message": f"TrackFlow Settings accessible, tracking enabled: {settings.enable_tracking}"
                }
            else:
                results["diagnostics"]["settings"] = {
                    "status": False,
                    "message": "TrackFlow Settings record does not exist"
                }
        except Exception as e:
            results["diagnostics"]["settings"] = {
                "status": False,
                "message": f"Settings access error: {str(e)}"
            }
        
        # Test after_request hook
        try:
            from trackflow.tracking import after_request
            # Create a mock response
            mock_response = {"status": "ok"}
            result = after_request(mock_response)
            results["diagnostics"]["after_request_hook"] = {
                "status": result == mock_response,
                "message": "after_request hook can be called successfully"
            }
        except Exception as e:
            results["diagnostics"]["after_request_hook"] = {
                "status": False,
                "message": f"after_request hook error: {str(e)}",
                "traceback": traceback.format_exc()
            }
        
        return results
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }
