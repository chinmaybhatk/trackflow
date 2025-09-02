import frappe
from frappe import _
from frappe.utils import getdate, add_days, nowdate
import json

@frappe.whitelist()
def get_campaign_stats(campaign_name):
    """Get campaign statistics"""
    try:
        # Get campaign details
        campaign = frappe.get_doc("Link Campaign", campaign_name)
        
        # Get click statistics
        clicks = frappe.db.sql("""
            SELECT 
                COUNT(*) as total_clicks,
                COUNT(DISTINCT visitor_id) as unique_visitors,
                COUNT(DISTINCT DATE(click_timestamp)) as active_days
            FROM `tabClick Event`
            WHERE campaign = %s
        """, campaign_name, as_dict=True)[0]
        
        # Get tracked links for this campaign
        tracked_links = frappe.db.sql("""
            SELECT 
                tl.name,
                tl.short_code,
                tl.custom_identifier,
                tl.click_count,
                tl.unique_visitors,
                tl.status
            FROM `tabTracked Link` tl
            WHERE tl.campaign = %s
            ORDER BY tl.click_count DESC
        """, campaign_name, as_dict=True)
        
        # Get conversions
        conversions = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabClick Event`
            WHERE campaign = %s AND led_to_conversion = 1
        """, campaign_name)[0][0] or 0
        
        # Calculate conversion rate
        conversion_rate = 0
        if clicks["unique_visitors"] > 0:
            conversion_rate = (conversions / clicks["unique_visitors"]) * 100
        
        return {
            "campaign": campaign.as_dict(),
            "stats": {
                "total_clicks": clicks["total_clicks"] or 0,
                "unique_visitors": clicks["unique_visitors"] or 0,
                "active_days": clicks["active_days"] or 0,
                "conversions": conversions,
                "conversion_rate": round(conversion_rate, 2),
                "tracked_links_count": len(tracked_links)
            },
            "tracked_links": tracked_links
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Campaign Stats Error")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_analytics(period="7days", metrics=None):
    """Get analytics dashboard data"""
    try:
        # Calculate date range
        to_date = getdate(nowdate())
        if period == "today":
            from_date = to_date
        elif period == "7days":
            from_date = add_days(to_date, -7)
        elif period == "30days":
            from_date = add_days(to_date, -30)
        elif period == "90days":
            from_date = add_days(to_date, -90)
        else:
            from_date = add_days(to_date, -7)
        
        data = {
            "period": period,
            "from_date": str(from_date),
            "to_date": str(to_date)
        }
        
        # Traffic metrics
        data["traffic"] = get_traffic_metrics(from_date, to_date)
        
        # Conversion metrics
        data["conversions"] = get_conversion_metrics(from_date, to_date)
        
        # Campaign metrics
        data["campaigns"] = get_top_campaigns(from_date, to_date)
        
        # Source/Medium breakdown
        data["sources"] = get_source_breakdown(from_date, to_date)
        
        # Time series data
        data["timeseries"] = get_timeseries_data(from_date, to_date)
        
        return data
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Analytics Error")
        return {"status": "error", "message": str(e)}

def get_traffic_metrics(from_date, to_date):
    """Get traffic metrics for period"""
    metrics = {}
    
    # Total clicks
    metrics["total_clicks"] = frappe.db.sql("""
        SELECT COUNT(*) FROM `tabClick Event`
        WHERE DATE(creation) BETWEEN %s AND %s
    """, (from_date, to_date))[0][0] or 0
    
    # Unique visitors
    metrics["unique_visitors"] = frappe.db.sql("""
        SELECT COUNT(DISTINCT visitor_id) FROM `tabClick Event`
        WHERE DATE(creation) BETWEEN %s AND %s
    """, (from_date, to_date))[0][0] or 0
    
    # Average clicks per visitor
    metrics["avg_clicks_per_visitor"] = (
        metrics["total_clicks"] / metrics["unique_visitors"] 
        if metrics["unique_visitors"] else 0
    )
    
    # New vs returning visitors
    new_visitors = frappe.db.sql("""
        SELECT COUNT(DISTINCT visitor_id) FROM `tabClick Event`
        WHERE DATE(creation) BETWEEN %s AND %s
        AND visitor_id NOT IN (
            SELECT DISTINCT visitor_id FROM `tabClick Event`
            WHERE DATE(creation) < %s
        )
    """, (from_date, to_date, from_date))[0][0] or 0
    
    metrics["new_visitors"] = new_visitors
    metrics["returning_visitors"] = metrics["unique_visitors"] - new_visitors
    
    return metrics

def get_conversion_metrics(from_date, to_date):
    """Get conversion metrics for period"""
    metrics = {}
    
    # Total conversions
    metrics["total_conversions"] = frappe.db.sql("""
        SELECT COUNT(*) FROM `tabLink Conversion`
        WHERE DATE(creation) BETWEEN %s AND %s
    """, (from_date, to_date))[0][0] or 0
    
    # Conversion value
    metrics["total_value"] = frappe.db.sql("""
        SELECT COALESCE(SUM(conversion_value), 0) FROM `tabLink Conversion`
        WHERE DATE(creation) BETWEEN %s AND %s
    """, (from_date, to_date))[0][0] or 0
    
    # Conversion types breakdown
    conversion_types = frappe.db.sql("""
        SELECT conversion_type, COUNT(*) as count
        FROM `tabLink Conversion`
        WHERE DATE(creation) BETWEEN %s AND %s
        GROUP BY conversion_type
    """, (from_date, to_date), as_dict=True)
    
    metrics["by_type"] = {ct["conversion_type"]: ct["count"] for ct in conversion_types}
    
    # Conversion rate
    clicks = frappe.db.sql("""
        SELECT COUNT(DISTINCT visitor_id) FROM `tabClick Event`
        WHERE DATE(creation) BETWEEN %s AND %s
    """, (from_date, to_date))[0][0] or 0
    
    metrics["conversion_rate"] = (
        (metrics["total_conversions"] / clicks * 100) if clicks else 0
    )
    
    return metrics

def get_top_campaigns(from_date, to_date):
    """Get top performing campaigns"""
    campaigns = frappe.db.sql("""
        SELECT 
            ce.campaign,
            COUNT(DISTINCT ce.visitor_id) as visitors,
            COUNT(ce.name) as clicks,
            COUNT(DISTINCT lc.name) as conversions,
            COALESCE(SUM(lc.conversion_value), 0) as revenue
        FROM `tabClick Event` ce
        LEFT JOIN `tabLink Conversion` lc ON lc.campaign = ce.campaign
        WHERE DATE(ce.creation) BETWEEN %s AND %s
        AND ce.campaign IS NOT NULL
        GROUP BY ce.campaign
        ORDER BY clicks DESC
        LIMIT 10
    """, (from_date, to_date), as_dict=True)
    
    for campaign in campaigns:
        campaign["conversion_rate"] = (
            (campaign["conversions"] / campaign["clicks"] * 100) 
            if campaign["clicks"] else 0
        )
    
    return campaigns

def get_source_breakdown(from_date, to_date):
    """Get traffic source breakdown"""
    sources = frappe.db.sql("""
        SELECT 
            COALESCE(utm_source, 'direct') as source,
            COALESCE(utm_medium, 'none') as medium,
            COUNT(*) as clicks,
            COUNT(DISTINCT visitor_id) as visitors
        FROM `tabClick Event`
        WHERE DATE(creation) BETWEEN %s AND %s
        GROUP BY utm_source, utm_medium
        ORDER BY clicks DESC
        LIMIT 20
    """, (from_date, to_date), as_dict=True)
    
    return sources

def get_timeseries_data(from_date, to_date):
    """Get time series data for charts"""
    # Daily clicks and conversions
    daily_data = frappe.db.sql("""
        SELECT 
            DATE(ce.creation) as date,
            COUNT(DISTINCT ce.name) as clicks,
            COUNT(DISTINCT ce.visitor_id) as visitors,
            COUNT(DISTINCT lc.name) as conversions
        FROM `tabClick Event` ce
        LEFT JOIN `tabLink Conversion` lc 
            ON DATE(lc.creation) = DATE(ce.creation)
        WHERE DATE(ce.creation) BETWEEN %s AND %s
        GROUP BY DATE(ce.creation)
        ORDER BY date
    """, (from_date, to_date), as_dict=True)
    
    return daily_data

@frappe.whitelist()
def get_visitor_journey(visitor_id):
    """Get complete journey for a visitor"""
    try:
        # Get all touchpoints
        touchpoints = frappe.db.sql("""
            SELECT 
                'click' as type,
                creation as timestamp,
                tracked_link,
                utm_source,
                utm_medium,
                utm_campaign,
                page_url,
                referrer
            FROM `tabClick Event`
            WHERE visitor_id = %s
            
            UNION ALL
            
            SELECT 
                'conversion' as type,
                creation as timestamp,
                document_name as tracked_link,
                source as utm_source,
                medium as utm_medium,
                campaign as utm_campaign,
                NULL as page_url,
                NULL as referrer
            FROM `tabLink Conversion`
            WHERE visitor_id = %s
            
            ORDER BY timestamp
        """, (visitor_id, visitor_id), as_dict=True)
        
        # Get visitor info
        visitor_info = {
            "id": visitor_id,
            "first_seen": touchpoints[0]["timestamp"] if touchpoints else None,
            "last_seen": touchpoints[-1]["timestamp"] if touchpoints else None,
            "total_touchpoints": len(touchpoints)
        }
        
        # Check if converted
        lead = frappe.db.get_value("CRM Lead", 
                                  {"custom_trackflow_visitor_id": visitor_id}, 
                                  ["name", "lead_name", "status"])
        
        if lead:
            visitor_info["lead"] = lead
            
        deal = frappe.db.get_value("CRM Deal",
                                  {"custom_trackflow_visitor_id": visitor_id},
                                  ["name", "deal_name", "status", "annual_revenue"])
        
        if deal:
            visitor_info["deal"] = deal
            
        return {
            "visitor": visitor_info,
            "journey": touchpoints
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Visitor Journey Error")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def export_analytics(format="csv", **kwargs):
    """Export analytics data"""
    try:
        data = get_analytics(**kwargs)
        
        if format == "csv":
            import csv
            from io import StringIO
            
            output = StringIO()
            writer = csv.writer(output)
            
            # Write headers
            writer.writerow(["Metric", "Value"])
            
            # Traffic metrics
            writer.writerow(["Traffic Metrics", ""])
            for key, value in data["traffic"].items():
                writer.writerow([key.replace("_", " ").title(), value])
                
            # Conversion metrics
            writer.writerow(["", ""])
            writer.writerow(["Conversion Metrics", ""])
            for key, value in data["conversions"].items():
                if isinstance(value, dict):
                    for k, v in value.items():
                        writer.writerow([f"{key} - {k}", v])
                else:
                    writer.writerow([key.replace("_", " ").title(), value])
                    
            return output.getvalue()
            
        else:
            return json.dumps(data, indent=2)
            
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Export Analytics Error")
        return {"status": "error", "message": str(e)}
