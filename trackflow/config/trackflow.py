from frappe import _

def get_data():
    return [
        {
            "label": _("Links"),
            "items": [
                {
                    "type": "doctype",
                    "name": "Tracked Link",
                    "description": _("Create and manage tracked links"),
                    "onboard": 1,
                },
                {
                    "type": "doctype",
                    "name": "Link Campaign",
                    "description": _("Organize links into campaigns"),
                    "onboard": 1,
                },
                {
                    "type": "doctype",
                    "name": "Link Template",
                    "description": _("Reusable UTM templates"),
                }
            ]
        },
        {
            "label": _("Analytics"),
            "items": [
                {
                    "type": "doctype",
                    "name": "Click Event",
                    "description": _("Track link clicks and events"),
                },
                {
                    "type": "report",
                    "name": "Link Performance",
                    "doctype": "Tracked Link",
                    "is_query_report": True,
                },
                {
                    "type": "report",
                    "name": "Campaign Analytics",
                    "doctype": "Link Campaign",
                    "is_query_report": True,
                },
                {
                    "type": "page",
                    "name": "trackflow-dashboard",
                    "label": _("TrackFlow Dashboard"),
                    "description": _("Real-time analytics dashboard"),
                }
            ]
        },
        {
            "label": _("Attribution"),
            "items": [
                {
                    "type": "report",
                    "name": "Lead Attribution",
                    "doctype": "Lead",
                    "is_query_report": True,
                },
                {
                    "type": "report",
                    "name": "Deal Attribution",
                    "doctype": "Deal",
                    "is_query_report": True,
                },
                {
                    "type": "doctype",
                    "name": "Attribution Model",
                    "description": _("Configure attribution models"),
                }
            ]
        },
        {
            "label": _("Settings"),
            "items": [
                {
                    "type": "doctype",
                    "name": "TrackFlow Settings",
                    "description": _("Configure TrackFlow"),
                },
                {
                    "type": "doctype",
                    "name": "Domain Configuration",
                    "description": _("Manage tracking domains"),
                },
                {
                    "type": "doctype",
                    "name": "Integration Settings",
                    "description": _("Third-party integrations"),
                }
            ]
        }
    ]