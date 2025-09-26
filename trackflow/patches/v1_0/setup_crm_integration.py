import frappe

def execute():
    """Set up CRM workspace integration for TrackFlow"""
    
    # Import the setup function from install.py
    from trackflow.install import setup_crm_integration
    
    # Run the CRM integration setup
    setup_crm_integration()
    
    # Clear cache to ensure changes take effect
    frappe.clear_cache()
    
    print("CRM integration setup completed")