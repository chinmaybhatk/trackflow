import frappe

def execute():
    """Force TrackFlow integration into CRM workspace"""
    
    try:
        # Check if CRM workspace exists
        if not frappe.db.exists("Workspace", "CRM"):
            print("CRM workspace not found, skipping TrackFlow integration")
            return
            
        # Get CRM workspace
        crm_workspace = frappe.get_doc("Workspace", "CRM")
        
        # Check if TrackFlow links already exist
        trackflow_exists = False
        for link in crm_workspace.links:
            if link.get('label') == 'TrackFlow Analytics':
                trackflow_exists = True
                break
        
        if trackflow_exists:
            print("TrackFlow links already exist in CRM workspace")
            return
            
        # Add TrackFlow links to CRM workspace
        trackflow_links = [
            {
                "type": "Card Break",
                "label": "TrackFlow Analytics",
                "hidden": 0,
                "onboard": 0,
                "idx": len(crm_workspace.links) + 1
            },
            {
                "type": "Link",
                "link_type": "DocType",
                "link_to": "Link Campaign",
                "label": "Campaigns",
                "hidden": 0,
                "onboard": 1,
                "idx": len(crm_workspace.links) + 2
            },
            {
                "type": "Link", 
                "link_type": "DocType",
                "link_to": "Tracked Link",
                "label": "Tracked Links",
                "hidden": 0,
                "onboard": 1,
                "idx": len(crm_workspace.links) + 3
            },
            {
                "type": "Link",
                "link_type": "DocType", 
                "link_to": "Click Event",
                "label": "Click Analytics",
                "hidden": 0,
                "onboard": 0,
                "idx": len(crm_workspace.links) + 4
            }
        ]
        
        # Append links to workspace
        for link in trackflow_links:
            crm_workspace.append("links", link)
            
        # Save workspace
        crm_workspace.save(ignore_permissions=True)
        frappe.db.commit()
        
        print("✓ TrackFlow successfully integrated into CRM workspace")
        print(f"Added {len(trackflow_links)} TrackFlow links to CRM")
        
        # Clear cache to ensure UI updates
        frappe.clear_cache()
        
    except Exception as e:
        frappe.log_error(f"Error in force_crm_workspace_integration: {str(e)}", "TrackFlow Patch")
        print(f"Error integrating TrackFlow into CRM workspace: {str(e)}")