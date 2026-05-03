"""
Notifications module for TrackFlow
"""

import frappe
from frappe import _


def get_notification_config():
    """Get notification configuration for TrackFlow"""
    return {
        "for_doctype": {
            "Link Campaign": {
                "status": ("in", ["Active", "Paused"]),
            },
            "Tracked Link": {
                "click_count": (">", 100),
            },
        }
    }


def send_weekly_report():
    """Send weekly analytics report — placeholder"""
    pass
