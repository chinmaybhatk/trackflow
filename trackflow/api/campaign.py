import frappe
from frappe import _
from frappe.utils import getdate, add_days, nowdate

@frappe.whitelist()
def create_campaign(name, start_date=None, end_date=None, budget=0, channel=None, description=None):
    """Create a new link campaign"""
    try:
        campaign = frappe.new_doc("Link Campaign")
        campaign.campaign_name = name
        campaign.start_date = start_date or nowdate()
        campaign.end_date = end_date
        campaign.budget = budget
        campaign.channel = channel
        campaign.description = description
        campaign.status = "Active"
        campaign.insert()
        
        return {
            "status": "success",
            "campaign": campaign.name,
            "message": _("Campaign created successfully")
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Create Campaign Error")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_campaign_performance(campaign_name=None, from_date=None, to_date=None):
    """Get campaign performance metrics"""
    try:
        filters = {}
        if campaign_name:
            filters["campaign"] = campaign_name
        if from_date:
            filters["creation"] = [">=", from_date]
        if to_date:
            if "creation" in filters:
                filters["creation"] = ["between", [from_date, to_date]]
            else:
                filters["creation"] = ["<=", to_date]
        
        # Get metrics
        clicks = frappe.db.count("Click Event", filters)
        unique_visitors = frappe.db.sql("""
            SELECT COUNT(DISTINCT visitor_id) 
            FROM `tabClick Event` 
            WHERE campaign = %s
        """, campaign_name)[0][0] if campaign_name else 0
        
        conversions = frappe.db.count("Link Conversion", filters)
        
        # Calculate revenue
        revenue = frappe.db.sql("""
            SELECT SUM(conversion_value) 
            FROM `tabLink Conversion` 
            WHERE campaign = %s
        """, campaign_name)[0][0] or 0 if campaign_name else 0
        
        # Get campaign budget
        budget = 0
        if campaign_name:
            campaign = frappe.get_doc("Link Campaign", campaign_name)
            budget = campaign.budget
        
        return {
            "metrics": {
                "clicks": clicks,
                "unique_visitors": unique_visitors,
                "conversions": conversions,
                "conversion_rate": (conversions / clicks * 100) if clicks else 0,
                "revenue": revenue,
                "roi": ((revenue - budget) / budget * 100) if budget else 0,
                "cost_per_click": (budget / clicks) if clicks else 0,
                "cost_per_conversion": (budget / conversions) if conversions else 0
            }
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Campaign Performance Error")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_campaign_list():
    """Get list of all campaigns with basic metrics"""
    try:
        campaigns = frappe.db.sql("""
            SELECT 
                c.name,
                c.campaign_name,
                c.status,
                c.start_date,
                c.end_date,
                c.budget,
                c.channel,
                COUNT(DISTINCT ce.visitor_id) as visitors,
                COUNT(ce.name) as clicks,
                COUNT(DISTINCT lc.name) as conversions
            FROM `tabLink Campaign` c
            LEFT JOIN `tabClick Event` ce ON ce.campaign = c.name
            LEFT JOIN `tabLink Conversion` lc ON lc.campaign = c.name
            GROUP BY c.name
            ORDER BY c.creation DESC
        """, as_dict=True)
        
        return {"campaigns": campaigns}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Campaign List Error")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def update_campaign_status(campaign_name, status):
    """Update campaign status"""
    try:
        if status not in ["Active", "Paused", "Completed", "Cancelled"]:
            frappe.throw(_("Invalid status"))
        
        frappe.db.set_value("Link Campaign", campaign_name, "status", status)
        frappe.db.commit()
        
        return {
            "status": "success",
            "message": _("Campaign status updated")
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Update Campaign Status Error")
        return {"status": "error", "message": str(e)}
