import frappe


def bootinfo(bootinfo):
    """Add TrackFlow configuration to bootinfo for CRM integration"""
    try:
        if not frappe.has_permission("Link Campaign", "read"):
            return
    except frappe.PermissionError:
        return

    bootinfo["trackflow_enabled"] = True

    try:
        settings = frappe.get_single("TrackFlow Settings")
        bootinfo["trackflow_settings"] = {
            "enable_tracking": getattr(settings, "enable_tracking", True),
            "default_attribution_model": getattr(
                settings, "default_attribution_model", "Last Touch"
            ),
        }
    except Exception:
        bootinfo["trackflow_settings"] = {
            "enable_tracking": True,
            "default_attribution_model": "Last Touch",
        }
