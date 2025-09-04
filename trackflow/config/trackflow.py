from frappe import _

def get_data():
    """Returns configuration for TrackFlow module in CRM sidebar"""
    return [
        {
            "label": _("TrackFlow"),
            "icon": "fa fa-link",
            "items": [
                {
                    "type": "doctype",
                    "name": "Link Campaign",
                    "label": _("Campaigns"),
                    "description": _("Manage link tracking campaigns"),
                    "onboard": 1,
                },
                {
                    "type": "doctype",
                    "name": "Tracked Link",
                    "label": _("Tracked Links"),
                    "description": _("View and manage tracked links"),
                    "onboard": 1,
                },
                {
                    "type": "doctype",
                    "name": "Visitor Session",
                    "label": _("Visitor Sessions"),
                    "description": _("Track visitor behavior"),
                },
                {
                    "type": "doctype",
                    "name": "Click Event",
                    "label": _("Click Events"),
                    "description": _("View all click events"),
                },
                {
                    "type": "report",
                    "name": "Campaign Performance",
                    "label": _("Campaign Analytics"),
                    "is_query_report": True,
                    "reference_doctype": "Link Campaign",
                },
                {
                    "type": "report",
                    "name": "Attribution Analysis",
                    "label": _("Attribution Report"),
                    "is_query_report": True,
                    "reference_doctype": "CRM Deal",
                },
                {
                    "type": "page",
                    "name": "trackflow-dashboard",
                    "label": _("TrackFlow Dashboard"),
                    "icon": "fa fa-dashboard",
                }
            ]
        }
    ]
