import frappe
from frappe import _

def get_context(context):
    """FCRM-style tracked links page"""
    context.no_cache = 1
    context.show_sidebar = False
    
    try:
        # Get links with stats
        links = get_links_with_stats()
        
        context.update({
            "title": _("TrackFlow Links"),
            "links": links,
            "page_name": "links"
        })
        
    except Exception as e:
        frappe.log_error(f"Error in links page: {str(e)}", "TrackFlow Links")
        context.update({
            "title": _("TrackFlow Links"),
            "links": [],
            "error": str(e)
        })
    
    return context

def get_links_with_stats():
    """Get tracked links with click statistics"""
    links = frappe.get_all(
        "Tracked Link",
        fields=[
            "name", "link_name", "target_url", "short_code", "campaign",
            "status", "click_count", "creation", "modified", "qr_code"
        ],
        order_by="modified desc"
    )
    
    for link in links:
        # Get recent click stats
        recent_stats = frappe.db.sql("""
            SELECT 
                COUNT(*) as recent_clicks,
                COUNT(DISTINCT visitor) as unique_visitors_recent
            FROM `tabClick Event` 
            WHERE tracked_link = %s 
            AND DATE(creation) >= DATE_SUB(CURDATE(), INTERVAL 7 DAYS)
        """, link.name, as_dict=True)
        
        if recent_stats:
            link.recent_clicks = recent_stats[0].recent_clicks or 0
            link.unique_visitors_recent = recent_stats[0].unique_visitors_recent or 0
        else:
            link.recent_clicks = 0
            link.unique_visitors_recent = 0
            
        # Get campaign name
        if link.campaign:
            campaign_name = frappe.db.get_value("Link Campaign", link.campaign, "campaign_name")
            link.campaign_display = campaign_name or link.campaign
        else:
            link.campaign_display = "No Campaign"
            
        # Generate full short URL
        site_url = frappe.utils.get_url()
        link.short_url = f"{site_url}/r/{link.short_code}"
        
        # Get top referrers
        top_referrers = frappe.db.sql("""
            SELECT referrer, COUNT(*) as count
            FROM `tabClick Event`
            WHERE tracked_link = %s AND referrer IS NOT NULL AND referrer != ''
            GROUP BY referrer
            ORDER BY count DESC
            LIMIT 3
        """, link.name, as_dict=True)
        
        link.top_referrers = top_referrers
    
    return links

@frappe.whitelist()
def get_link_analytics(link_name):
    """Get detailed analytics for a specific link"""
    if not frappe.db.exists("Tracked Link", link_name):
        frappe.throw(_("Link not found"))
        
    link = frappe.get_doc("Tracked Link", link_name)
    
    # Get click analytics by day (last 30 days)
    daily_clicks = frappe.db.sql("""
        SELECT 
            DATE(creation) as date,
            COUNT(*) as clicks,
            COUNT(DISTINCT visitor) as unique_visitors
        FROM `tabClick Event` 
        WHERE tracked_link = %s 
        AND DATE(creation) >= DATE_SUB(CURDATE(), INTERVAL 30 DAYS)
        GROUP BY DATE(creation)
        ORDER BY date DESC
    """, link_name, as_dict=True)
    
    # Get geographic data
    geo_data = frappe.db.sql("""
        SELECT 
            country,
            COUNT(*) as clicks
        FROM `tabClick Event` 
        WHERE tracked_link = %s AND country IS NOT NULL
        GROUP BY country
        ORDER BY clicks DESC
        LIMIT 10
    """, link_name, as_dict=True)
    
    # Get device/browser stats
    device_stats = frappe.db.sql("""
        SELECT 
            device_type,
            browser,
            COUNT(*) as clicks
        FROM `tabClick Event` 
        WHERE tracked_link = %s
        GROUP BY device_type, browser
        ORDER BY clicks DESC
    """, link_name, as_dict=True)
    
    return {
        "link": link.as_dict(),
        "daily_clicks": daily_clicks,
        "geo_data": geo_data,
        "device_stats": device_stats
    }

@frappe.whitelist()
def copy_link(link_name):
    """Return the short URL for copying"""
    if not frappe.db.exists("Tracked Link", link_name):
        frappe.throw(_("Link not found"))
        
    short_code = frappe.db.get_value("Tracked Link", link_name, "short_code")
    site_url = frappe.utils.get_url()
    return f"{site_url}/r/{short_code}"