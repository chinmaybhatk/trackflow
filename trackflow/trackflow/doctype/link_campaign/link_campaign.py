# Copyright (c) 2024, Chinmay Bhat and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class LinkCampaign(Document):
    def validate(self):
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                frappe.throw("End Date cannot be before Start Date")


def get_permission_query_conditions(user):
    """Return permission query conditions for Link Campaign doctype"""
    if not user:
        user = frappe.session.user
    
    # Everyone can see link campaigns
    return None
