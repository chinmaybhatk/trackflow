import frappe
from frappe import _

@frappe.whitelist()
def bulk_generate_links(campaign, identifiers):
    """Generate multiple tracked links for a campaign"""
    if isinstance(identifiers, str):
        import json
        identifiers = json.loads(identifiers)
    
    created_links = []
    
    for identifier in identifiers:
        # Check if link already exists
        existing = frappe.db.exists("Tracked Link", {
            "campaign": campaign,
            "custom_identifier": identifier
        })
        
        if not existing:
            link = frappe.new_doc("Tracked Link")
            link.campaign = campaign
            link.custom_identifier = identifier
            link.destination_url = f"https://example.com/{identifier}"  # Default URL
            link.status = "Active"
            link.insert()
            created_links.append(link.name)
    
    frappe.db.commit()
    return {"created": created_links, "count": len(created_links)}

@frappe.whitelist()
def get_tracking_script(campaign):
    """Get JavaScript tracking script for a campaign"""
    return f"""
<!-- TrackFlow Tracking Script -->
<script>
(function() {{
    var tf_campaign = '{campaign}';
    var tf_visitor = localStorage.getItem('tf_visitor_id') || 
                     'v_' + Math.random().toString(36).substr(2, 9);
    localStorage.setItem('tf_visitor_id', tf_visitor);
    
    // Track page view
    fetch('/api/method/trackflow.api.tracking.track_event', {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{
            event_type: 'page_view',
            campaign: tf_campaign,
            visitor_id: tf_visitor,
            page_url: window.location.href,
            referrer: document.referrer
        }})
    }});
}})();
</script>
"""
