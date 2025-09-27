import frappe
from frappe import _

def crm_lead_dashboard(data=None):
    """Dashboard configuration for CRM Lead with TrackFlow integration"""
    return {
        "heatmap": False,
        "heatmap_message": _("This is based on the date of creation of Lead"),
        "fieldname": "creation", 
        "transactions": [
            {
                "label": _("TrackFlow Attribution"),
                "items": ["Click Event", "Visitor Session", "Attribution Model"]
            },
            {
                "label": _("Campaign Performance"),
                "items": ["Link Campaign", "Tracked Link"]
            }
        ]
    }

def crm_deal_dashboard(data=None):
    """Dashboard configuration for CRM Deal with TrackFlow integration"""
    return {
        "heatmap": True,
        "heatmap_message": _("This is based on the date of creation of Deal"),
        "fieldname": "creation",
        "transactions": [
            {
                "label": _("TrackFlow Attribution"), 
                "items": ["Deal Attribution", "Click Event", "Link Campaign"]
            },
            {
                "label": _("Conversion Tracking"),
                "items": ["Link Conversion", "Visitor"]
            }
        ]
    }