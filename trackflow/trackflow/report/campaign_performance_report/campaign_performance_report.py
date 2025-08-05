# Copyright (c) 2024, TrackFlow and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate, add_days

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {
            "fieldname": "campaign",
            "label": _("Campaign"),
            "fieldtype": "Link",
            "options": "Campaign",
            "width": 200
        },
        {
            "fieldname": "source",
            "label": _("Source"),
            "fieldtype": "Data",
            "width": 120
        },
        {
            "fieldname": "medium",
            "label": _("Medium"),
            "fieldtype": "Data",
            "width": 120
        },
        {
            "fieldname": "total_clicks",
            "label": _("Total Clicks"),
            "fieldtype": "Int",
            "width": 100
        },
        {
            "fieldname": "unique_visitors",
            "label": _("Unique Visitors"),
            "fieldtype": "Int",
            "width": 120
        },
        {
            "fieldname": "conversions",
            "label": _("Conversions"),
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
            "fieldname": "total_value",
            "label": _("Total Value"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "cost",
            "label": _("Cost"),
            "fieldtype": "Currency",
            "width": 100
        },
        {
            "fieldname": "roi",
            "label": _("ROI %"),
            "fieldtype": "Percent",
            "width": 100
        },
        {
            "fieldname": "cpc",
            "label": _("Cost Per Click"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "cpa",
            "label": _("Cost Per Acquisition"),
            "fieldtype": "Currency",
            "width": 150
        }
    ]

def get_data(filters):
    conditions = get_conditions(filters)
    
    data = frappe.db.sql("""
        SELECT
            c.name as campaign,
            c.source,
            c.medium,
            COALESCE(SUM(tl.total_clicks), 0) as total_clicks,
            COUNT(DISTINCT v.name) as unique_visitors,
            COUNT(DISTINCT conv.name) as conversions,
            COALESCE(SUM(conv.conversion_value), 0) as total_value,
            c.total_cost as cost
        FROM `tabCampaign` c
        LEFT JOIN `tabTracking Link` tl ON tl.campaign = c.name
        LEFT JOIN `tabPage View` pv ON pv.tracking_link = tl.name
        LEFT JOIN `tabVisitor` v ON pv.visitor = v.name
        LEFT JOIN `tabConversion` conv ON conv.visitor = v.name
            AND conv.campaign = c.campaign_name
        WHERE c.docstatus < 2 {conditions}
        GROUP BY c.name
        ORDER BY total_clicks DESC
    """.format(conditions=conditions), filters, as_dict=True)
    
    # Calculate additional metrics
    for row in data:
        if row.unique_visitors:
            row.conversion_rate = flt(row.conversions) / flt(row.unique_visitors) * 100
        else:
            row.conversion_rate = 0
        
        if row.cost:
            row.roi = (flt(row.total_value) - flt(row.cost)) / flt(row.cost) * 100
            if row.total_clicks:
                row.cpc = flt(row.cost) / flt(row.total_clicks)
            if row.conversions:
                row.cpa = flt(row.cost) / flt(row.conversions)
        else:
            row.roi = 0
            row.cpc = 0
            row.cpa = 0
    
    return data

def get_conditions(filters):
    conditions = ""
    
    if filters.get("campaign"):
        conditions += " AND c.name = %(campaign)s"
    
    if filters.get("source"):
        conditions += " AND c.source = %(source)s"
    
    if filters.get("medium"):
        conditions += " AND c.medium = %(medium)s"
    
    if filters.get("from_date"):
        conditions += " AND c.start_date >= %(from_date)s"
    
    if filters.get("to_date"):
        conditions += " AND c.start_date <= %(to_date)s"
    
    if filters.get("status"):
        conditions += " AND c.status = %(status)s"
    
    return conditions