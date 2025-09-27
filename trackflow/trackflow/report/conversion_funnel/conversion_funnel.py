import frappe
from frappe import _
import json
from datetime import datetime, timedelta

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_funnel_chart(filters)
    summary = get_summary(filters)
    
    return columns, data, None, chart, summary

def get_columns():
    return [
        {
            "fieldname": "stage",
            "label": _("Stage"),
            "fieldtype": "Data",
            "width": 200
        },
        {
            "fieldname": "visitors",
            "label": _("Visitors"),
            "fieldtype": "Int",
            "width": 100
        },
        {
            "fieldname": "conversion_rate",
            "label": _("Conversion Rate %"),
            "fieldtype": "Percent",
            "width": 120
        },
        {
            "fieldname": "drop_off_rate",
            "label": _("Drop-off Rate %"),
            "fieldtype": "Percent",
            "width": 120
        },
        {
            "fieldname": "avg_time_to_convert",
            "label": _("Avg Time to Convert"),
            "fieldtype": "Data",
            "width": 150
        },
        {
            "fieldname": "value",
            "label": _("Stage Value"),
            "fieldtype": "Currency",
            "width": 120
        }
    ]

def get_data(filters):
    conditions = get_conditions(filters)
    
    # Define funnel stages
    stages = [
        {"name": "Visited Site", "stage": "visited"},
        {"name": "Viewed Product/Service", "stage": "viewed"},
        {"name": "Submitted Form", "stage": "form_submitted"},
        {"name": "Became Lead", "stage": "lead_created"},
        {"name": "Converted to Deal", "stage": "deal_created"},
        {"name": "Deal Won", "stage": "deal_won"}
    ]
    
    data = []
    total_visitors = get_total_visitors(filters)
    previous_count = total_visitors
    
    for idx, stage in enumerate(stages):
        stage_data = get_stage_data(stage["stage"], filters)
        
        if stage_data:
            conversion_rate = (stage_data["count"] / total_visitors * 100) if total_visitors > 0 else 0
            drop_off_rate = ((previous_count - stage_data["count"]) / previous_count * 100) if previous_count > 0 else 0
            
            data.append({
                "stage": stage["name"],
                "visitors": stage_data["count"],
                "conversion_rate": conversion_rate,
                "drop_off_rate": drop_off_rate,
                "avg_time_to_convert": format_duration(stage_data.get("avg_time", 0)),
                "value": stage_data.get("value", 0)
            })
            
            previous_count = stage_data["count"]
    
    return data

def get_conditions(filters):
    conditions = []
    
    if filters.get("from_date"):
        conditions.append("creation >= %(from_date)s")
    
    if filters.get("to_date"):
        conditions.append("creation <= %(to_date)s")
    
    if filters.get("campaign"):
        conditions.append("campaign = %(campaign)s")
    
    return " AND " + " AND ".join(conditions) if conditions else ""

def get_total_visitors(filters):
    conditions = get_conditions(filters)
    
    result = frappe.db.sql("""
        SELECT COUNT(DISTINCT visitor_id) as count
        FROM `tabVisitor Session`
        WHERE docstatus < 2 {conditions}
    """.format(conditions=conditions), filters, as_dict=1)
    
    return result[0]["count"] if result else 0

def get_stage_data(stage, filters):
    conditions = get_conditions(filters)
    
    if stage == "visited":
        return frappe.db.sql("""
            SELECT 
                COUNT(DISTINCT visitor_id) as count,
                0 as avg_time,
                0 as value
            FROM `tabVisitor Session`
            WHERE docstatus < 2 {conditions}
        """.format(conditions=conditions), filters, as_dict=1)[0]
    
    elif stage == "viewed":
        return frappe.db.sql("""
            SELECT 
                COUNT(DISTINCT vs.visitor_id) as count,
                AVG(TIMESTAMPDIFF(SECOND, vs.creation, pv.creation)) as avg_time,
                0 as value
            FROM `tabVisitor Session` vs
            INNER JOIN `tabPage View` pv ON pv.session = vs.name
            WHERE vs.docstatus < 2 
            AND pv.page_type IN ('Product', 'Service', 'Solution')
            {conditions}
        """.format(conditions=conditions.replace("creation", "vs.creation")), filters, as_dict=1)[0]
    
    elif stage == "form_submitted":
        return frappe.db.sql("""
            SELECT 
                COUNT(DISTINCT c.visitor_id) as count,
                AVG(TIMESTAMPDIFF(SECOND, vs.creation, c.creation)) as avg_time,
                0 as value
            FROM `tabLink Conversion` c
            INNER JOIN `tabVisitor Session` vs ON vs.visitor_id = c.visitor_id
            WHERE c.docstatus < 2 
            AND c.conversion_type = 'Form Submission'
            {conditions}
        """.format(conditions=conditions.replace("creation", "c.creation")), filters, as_dict=1)[0]
    
    elif stage == "lead_created":
        return frappe.db.sql("""
            SELECT 
                COUNT(DISTINCT l.name) as count,
                AVG(TIMESTAMPDIFF(SECOND, vs.creation, l.creation)) as avg_time,
                0 as value
            FROM `tabLead` l
            INNER JOIN `tabLead Link Association` lla ON lla.lead = l.name
            INNER JOIN `tabVisitor Session` vs ON vs.visitor_id = lla.visitor_id
            WHERE l.docstatus < 2
            {conditions}
        """.format(conditions=conditions.replace("creation", "l.creation")), filters, as_dict=1)[0]
    
    elif stage == "deal_created":
        return frappe.db.sql("""
            SELECT 
                COUNT(DISTINCT d.name) as count,
                AVG(TIMESTAMPDIFF(SECOND, l.creation, d.creation)) as avg_time,
                SUM(d.opportunity_amount) as value
            FROM `tabOpportunity` d
            INNER JOIN `tabDeal Link Association` dla ON dla.deal = d.name
            INNER JOIN `tabLead` l ON l.name = d.party_name AND d.opportunity_from = 'Lead'
            WHERE d.docstatus < 2
            {conditions}
        """.format(conditions=conditions.replace("creation", "d.creation")), filters, as_dict=1)[0]
    
    elif stage == "deal_won":
        return frappe.db.sql("""
            SELECT 
                COUNT(DISTINCT d.name) as count,
                AVG(TIMESTAMPDIFF(SECOND, d.creation, d.modified)) as avg_time,
                SUM(d.opportunity_amount) as value
            FROM `tabOpportunity` d
            INNER JOIN `tabDeal Link Association` dla ON dla.deal = d.name
            WHERE d.docstatus < 2
            AND d.status = 'Closed'
            {conditions}
        """.format(conditions=conditions.replace("creation", "d.creation")), filters, as_dict=1)[0]
    
    return {"count": 0, "avg_time": 0, "value": 0}

def format_duration(seconds):
    if not seconds:
        return "0s"
    
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    
    if days:
        return f"{days}d {hours}h"
    elif hours:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"

def get_funnel_chart(filters):
    data = get_data(filters)
    
    return {
        "data": {
            "labels": [d["stage"] for d in data],
            "datasets": [{
                "name": "Conversion Funnel",
                "values": [d["visitors"] for d in data]
            }]
        },
        "type": "bar",
        "colors": ["#4CAF50"],
        "barOptions": {
            "spaceRatio": 0.2
        }
    }

def get_summary(filters):
    conditions = get_conditions(filters)
    
    # Get overall conversion metrics
    total_visitors = get_total_visitors(filters)
    
    leads_created = frappe.db.sql("""
        SELECT COUNT(DISTINCT l.name) as count
        FROM `tabLead` l
        INNER JOIN `tabLead Link Association` lla ON lla.lead = l.name
        WHERE l.docstatus < 2 {conditions}
    """.format(conditions=conditions.replace("creation", "l.creation")), filters, as_dict=1)[0]["count"]
    
    deals_created = frappe.db.sql("""
        SELECT COUNT(DISTINCT d.name) as count
        FROM `tabOpportunity` d
        INNER JOIN `tabDeal Link Association` dla ON dla.deal = d.name
        WHERE d.docstatus < 2 {conditions}
    """.format(conditions=conditions.replace("creation", "d.creation")), filters, as_dict=1)[0]["count"]
    
    deals_won = frappe.db.sql("""
        SELECT 
            COUNT(DISTINCT d.name) as count,
            COALESCE(SUM(d.opportunity_amount), 0) as total_value
        FROM `tabOpportunity` d
        INNER JOIN `tabDeal Link Association` dla ON dla.deal = d.name
        WHERE d.docstatus < 2
        AND d.status = 'Closed'
        {conditions}
    """.format(conditions=conditions.replace("creation", "d.creation")), filters, as_dict=1)[0]
    
    visitor_to_lead = (leads_created / total_visitors * 100) if total_visitors > 0 else 0
    lead_to_deal = (deals_created / leads_created * 100) if leads_created > 0 else 0
    deal_to_won = (deals_won["count"] / deals_created * 100) if deals_created > 0 else 0
    overall_conversion = (deals_won["count"] / total_visitors * 100) if total_visitors > 0 else 0
    
    summary = [
        {
            "value": total_visitors,
            "label": _("Total Visitors"),
            "datatype": "Int",
            "color": "blue"
        },
        {
            "value": round(visitor_to_lead, 2),
            "label": _("Visitor to Lead %"),
            "datatype": "Percent",
            "color": "orange"
        },
        {
            "value": round(lead_to_deal, 2),
            "label": _("Lead to Deal %"),
            "datatype": "Percent",
            "color": "yellow"
        },
        {
            "value": round(deal_to_won, 2),
            "label": _("Deal to Won %"),
            "datatype": "Percent",
            "color": "green"
        },
        {
            "value": round(overall_conversion, 2),
            "label": _("Overall Conversion %"),
            "datatype": "Percent",
            "color": "purple"
        },
        {
            "value": deals_won["total_value"],
            "label": _("Total Revenue"),
            "datatype": "Currency",
            "color": "green"
        }
    ]
    
    return summary
