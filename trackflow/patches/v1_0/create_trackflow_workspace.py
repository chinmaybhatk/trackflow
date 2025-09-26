import frappe

def execute():
    """Create a dedicated TrackFlow workspace with modern UI links"""
    
    try:
        # Check if TrackFlow workspace already exists
        if frappe.db.exists("Workspace", "TrackFlow"):
            print("TrackFlow workspace already exists")
            return
            
        # Create TrackFlow workspace
        workspace = frappe.new_doc("Workspace")
        workspace.update({
            "name": "TrackFlow",
            "title": "TrackFlow",
            "category": "Modules",
            "icon": "fa fa-bullhorn",
            "module": "TrackFlow",
            "public": 1,
            "content": "[]"
        })
        
        # Add workspace links
        workspace_links = [
            {
                "type": "Card Break",
                "label": "Marketing Attribution",
                "hidden": 0,
                "onboard": 0
            },
            {
                "type": "Link",
                "link_type": "DocType",
                "link_to": "Link Campaign",
                "label": "Campaigns",
                "hidden": 0,
                "onboard": 1
            },
            {
                "type": "Link",
                "link_type": "DocType", 
                "link_to": "Tracked Link",
                "label": "Tracked Links",
                "hidden": 0,
                "onboard": 1
            },
            {
                "type": "Link",
                "link_type": "DocType",
                "link_to": "Click Event",
                "label": "Click Analytics",
                "hidden": 0,
                "onboard": 0
            },
            {
                "type": "Link",
                "link_type": "DocType",
                "link_to": "Visitor",
                "label": "Visitors",
                "hidden": 0,
                "onboard": 0
            },
            {
                "type": "Card Break",
                "label": "Configuration",
                "hidden": 0,
                "onboard": 0
            },
            {
                "type": "Link",
                "link_type": "DocType",
                "link_to": "TrackFlow Settings",
                "label": "Settings",
                "hidden": 0,
                "onboard": 0
            },
            {
                "type": "Link",
                "link_type": "DocType",
                "link_to": "Attribution Model",
                "label": "Attribution Models",
                "hidden": 0,
                "onboard": 0
            }
        ]
        
        # Add links to workspace
        for link in workspace_links:
            workspace.append("links", link)
            
        # Add shortcuts
        shortcuts = [
            {
                "type": "DocType",
                "link_to": "Link Campaign",
                "label": "New Campaign"
            },
            {
                "type": "DocType", 
                "link_to": "Tracked Link",
                "label": "New Link"
            }
        ]
        
        for shortcut in shortcuts:
            workspace.append("shortcuts", shortcut)
            
        # Add roles
        workspace.append("roles", {"role": "System Manager"})
        workspace.append("roles", {"role": "TrackFlow Manager"})
        
        # Insert the workspace
        workspace.insert(ignore_permissions=True)
        frappe.db.commit()
        
        print("✓ Created dedicated TrackFlow workspace")
        print("✓ Added modern UI links and shortcuts")
        
        # Clear cache
        frappe.clear_cache()
        
    except Exception as e:
        frappe.log_error(f"Error creating TrackFlow workspace: {str(e)}", "TrackFlow Patch")
        print(f"Error creating TrackFlow workspace: {str(e)}")