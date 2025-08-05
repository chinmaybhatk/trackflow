# -*- coding: utf-8 -*-
# Copyright (c) 2024, TrackFlow and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class APIRequestLog(Document):
    def after_insert(self):
        """Clean up old logs"""
        # Keep only last 30 days of logs
        frappe.db.delete('API Request Log', {
            'timestamp': ('<=', frappe.utils.add_days(frappe.utils.now(), -30))
        })
