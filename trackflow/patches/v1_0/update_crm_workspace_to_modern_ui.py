import frappe

def execute():
    """Update CRM workspace links to use modern TrackFlow UI pages"""
    
    try:
        # Check if CRM workspace exists
        if not frappe.db.exists("Workspace", "CRM"):
            print("CRM workspace not found")
            return
            
        # Get CRM workspace
        crm_workspace = frappe.get_doc("Workspace", "CRM")
        
        # Find and update TrackFlow links
        updated_links = []
        trackflow_section_found = False
        
        for link in crm_workspace.links:
            if link.get('label') == 'TrackFlow Analytics':
                trackflow_section_found = True
                updated_links.append(link)  # Keep the card break as is
                
            elif link.get('label') == 'Campaigns' and trackflow_section_found:
                # Update to point to modern campaigns page
                link.type = 'Link'
                link.link_type = 'Page'
                link.link_to = '/campaigns'
                link.label = 'Campaigns'
                updated_links.append(link)
                
            elif link.get('label') == 'Tracked Links' and trackflow_section_found:
                # Update to point to modern links page
                link.type = 'Link'
                link.link_type = 'Page' 
                link.link_to = '/links'
                link.label = 'Tracked Links'
                updated_links.append(link)
                
            elif link.get('label') == 'Click Analytics' and trackflow_section_found:
                # Update to point to modern analytics page
                link.type = 'Link'
                link.link_type = 'Page'
                link.link_to = '/analytics' 
                link.label = 'Analytics'
                updated_links.append(link)
                trackflow_section_found = False  # Reset after processing TrackFlow section
                
            else:
                updated_links.append(link)
        
        # If no TrackFlow section exists, add it with modern links
        if not any(link.get('label') == 'TrackFlow Analytics' for link in updated_links):
            trackflow_links = [
                {
                    "type": "Card Break",
                    "label": "TrackFlow Analytics", 
                    "hidden": 0,
                    "onboard": 0,
                    "idx": len(updated_links) + 1
                },
                {
                    "type": "Link",
                    "link_type": "Page",
                    "link_to": "/campaigns",
                    "label": "Campaigns",
                    "hidden": 0,
                    "onboard": 0,
                    "idx": len(updated_links) + 2
                },
                {
                    "type": "Link",
                    "link_type": "Page", 
                    "link_to": "/links",
                    "label": "Tracked Links",
                    "hidden": 0,
                    "onboard": 0,
                    "idx": len(updated_links) + 3
                },
                {
                    "type": "Link",
                    "link_type": "Page",
                    "link_to": "/analytics",
                    "label": "Analytics",
                    "hidden": 0,
                    "onboard": 0,
                    "idx": len(updated_links) + 4
                }
            ]
            
            for link in trackflow_links:
                updated_links.append(link)
        
        # Clear existing links and add updated ones
        crm_workspace.links = []
        for link in updated_links:
            crm_workspace.append("links", link)
            
        # Save the workspace
        crm_workspace.save(ignore_permissions=True)
        frappe.db.commit()
        
        print("✓ Updated CRM workspace with modern TrackFlow UI links")
        print("✓ TrackFlow now uses FCRM-compatible pages")
        
        # Clear cache to ensure UI updates
        frappe.clear_cache()
        
    except Exception as e:
        frappe.log_error(f"Error updating CRM workspace: {str(e)}", "TrackFlow Patch")
        print(f"Error updating CRM workspace: {str(e)}")
        
        # Fallback: Try to add modern links without replacing existing ones
        try_fallback_update()