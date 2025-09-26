import frappe

def execute():
    """Fix IP range validation issues"""
    frappe.reload_doc("trackflow", "doctype", "internal_ip_range")
    frappe.reload_doc("trackflow", "doctype", "trackflow_settings")
    
    # Clear any cached data
    frappe.clear_cache()
    
    print("Fixed IP range validation issues")