import frappe
from frappe import _

@frappe.whitelist()
def bulk_generate_links(campaign, identifiers):
    """Generate multiple tracked links for a campaign"""
    if not campaign:
        frappe.throw(_("Campaign is required"))
    
    if not identifiers:
        frappe.throw(_("Identifiers are required"))
    
    # Parse identifiers (comma or newline separated)
    if isinstance(identifiers, str):
        identifiers = [x.strip() for x in identifiers.replace('\n', ',').split(',') if x.strip()]
    
    created_links = []
    
    for identifier in identifiers:
        try:
            # Check if link already exists
            if frappe.db.exists("Tracked Link", {"campaign": campaign, "custom_identifier": identifier}):
                continue
                
            # Create tracked link
            link = frappe.new_doc("Tracked Link")
            link.campaign = campaign
            link.custom_identifier = identifier
            link.destination_url = f"https://example.com/{identifier}"  # Default URL
            link.status = "Active"
            link.insert()
            created_links.append(link.name)
            
        except Exception as e:
            frappe.log_error(f"Error creating link for {identifier}: {str(e)}")
            
    frappe.db.commit()
    
    return {
        "created": len(created_links),
        "links": created_links
    }
