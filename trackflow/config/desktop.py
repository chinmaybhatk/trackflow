from frappe import _

def get_data():
    return [
        {
            "module_name": "TrackFlow",
            "category": "Modules",
            "label": _("TrackFlow"),
            "color": "#2563eb",
            "icon": "octicon octicon-graph",
            "type": "module",
            "description": "Smart link tracking and attribution for CRM",
            "onboard_present": 1
        }
    ]