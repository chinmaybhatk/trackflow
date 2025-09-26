import frappe
from frappe import _

def get_context(context):
    """FCRM-style campaigns page"""
    context.no_cache = 1
    context.show_sidebar = False
    
    try:
        # Get campaigns with stats
        campaigns = get_campaigns_with_stats()
        
        context.update({
            "title": _("TrackFlow Campaigns"),
            "campaigns": campaigns,
            "page_name": "campaigns"
        })
        
    except Exception as e:
        frappe.log_error(f"Error in campaigns page: {str(e)}", "TrackFlow Campaigns")
        context.update({
            "title": _("TrackFlow Campaigns"),
            "campaigns": [],
            "error": str(e)
        })
    
    return context

def get_campaigns_with_stats():
    """Get campaigns with click and conversion statistics"""
    campaigns = frappe.get_all(
        "Link Campaign",
        fields=[
            "name", "campaign_name", "description", "status", 
            "start_date", "end_date", "creation", "modified"
        ],
        order_by="modified desc"
    )
    
    for campaign in campaigns:
        # Get click statistics
        click_stats = frappe.db.sql("""
            SELECT 
                COUNT(*) as total_clicks,
                COUNT(DISTINCT visitor) as unique_visitors
            FROM `tabClick Event` 
            WHERE campaign = %s
        """, campaign.name, as_dict=True)
        
        if click_stats:
            campaign.total_clicks = click_stats[0].total_clicks or 0
            campaign.unique_visitors = click_stats[0].unique_visitors or 0
        else:
            campaign.total_clicks = 0
            campaign.unique_visitors = 0
            
        # Get conversion stats
        conversions = frappe.db.sql("""
            SELECT COUNT(*) as conversions
            FROM `tabConversion`
            WHERE campaign = %s
        """, campaign.name, as_dict=True)
        
        campaign.conversions = conversions[0].conversions if conversions else 0
        
        # Calculate conversion rate
        if campaign.unique_visitors > 0:
            campaign.conversion_rate = (campaign.conversions / campaign.unique_visitors) * 100
        else:
            campaign.conversion_rate = 0
            
        # Get links count
        links_count = frappe.db.count("Tracked Link", {"campaign": campaign.name})
        campaign.links_count = links_count
    
    return campaigns

@frappe.whitelist()
def get_campaign_data(campaign_name):
    """Get detailed campaign data for modal/detail view"""
    if not frappe.db.exists("Link Campaign", campaign_name):
        frappe.throw(_("Campaign not found"))
        
    campaign = frappe.get_doc("Link Campaign", campaign_name)
    
    # Get recent clicks
    recent_clicks = frappe.get_all(
        "Click Event",
        filters={"campaign": campaign_name},
        fields=["creation", "browser", "device_type", "country", "referrer"],
        order_by="creation desc",
        limit=10
    )
    
    # Get links
    links = frappe.get_all(
        "Tracked Link", 
        filters={"campaign": campaign_name},
        fields=["name", "short_code", "target_url", "click_count", "status"],
        order_by="creation desc"
    )
    
    return {
        "campaign": campaign.as_dict(),
        "recent_clicks": recent_clicks,
        "links": links
    }