import frappe

def bootinfo(bootinfo):
    """Add TrackFlow configuration to bootinfo for CRM integration"""
    
    # Check if user has access to TrackFlow
    if frappe.has_permission("Link Campaign", "read"):
        bootinfo["trackflow_enabled"] = True
        
        # Add TrackFlow settings to bootinfo
        try:
            settings = frappe.get_single("TrackFlow Settings")
            bootinfo["trackflow_settings"] = {
                "enable_tracking": getattr(settings, 'enable_tracking', True),
                "default_attribution_model": getattr(settings, 'default_attribution_model', 'Last Touch')
            }
        except Exception:
            bootinfo["trackflow_settings"] = {
                "enable_tracking": True,
                "default_attribution_model": "Last Touch"
            }
    
    return bootinfo