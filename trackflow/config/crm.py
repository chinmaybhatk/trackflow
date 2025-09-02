from frappe import _

def get_data():
    return [
        {
            "label": _("TrackFlow"),
            "items": [
                {
                    "type": "doctype",
                    "name": "Link Campaign",
                    "label": _("Link Campaign"),
                    "description": _("Create and manage marketing campaigns with trackable links"),
                    "onboard": 1,
                },
                {
                    "type": "doctype",
                    "name": "Tracked Link",
                    "label": _("Tracked Link"),
                    "description": _("Generate and manage trackable URLs for campaigns"),
                    "dependencies": ["Link Campaign"],
                    "onboard": 1,
                },
                {
                    "type": "doctype",
                    "name": "Click Event",
                    "label": _("Click Analytics"),
                    "description": _("View click events and visitor analytics"),
                    "dependencies": ["Tracked Link"],
                },
            ]
        },
        {
            "label": _("Attribution Reports"),
            "items": [
                {
                    "type": "report",
                    "name": "Campaign Performance",
                    "label": _("Campaign Performance"),
                    "doctype": "Link Campaign",
                    "is_query_report": True,
                    "description": _("View campaign metrics and ROI")
                },
                {
                    "type": "report",
                    "name": "Lead Attribution",
                    "label": _("Lead Attribution"),
                    "doctype": "CRM Lead",
                    "is_query_report": True,
                    "description": _("Track lead sources and attribution")
                },
                {
                    "type": "report",
                    "name": "Visitor Journey",
                    "label": _("Visitor Journey"),
                    "doctype": "Click Event",
                    "is_query_report": True,
                    "description": _("Analyze visitor paths and conversions")
                },
            ]
        }
    ]
