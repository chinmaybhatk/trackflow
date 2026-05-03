# Copyright (c) 2024, Chinmay Bhat and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Visitor(Document):
    def before_save(self):
        self.engagement_score = self.calculate_engagement_score()

    def calculate_engagement_score(self):
        """Lightweight 0-100 engagement score based on actual fields."""
        score = 0

        # Clicks (1 pt each, capped at 30)
        clicks = frappe.db.count("Click Event", {"visitor_id": self.visitor_id})
        score += min(clicks, 30)

        # Page views (0.5 pt each, capped at 20)
        page_views = self.page_views or 0
        score += min(page_views * 0.5, 20)

        # Has CRM lead linked (+30)
        if self.get("crm_lead"):
            score += 30

        # Conversion count (5 pt each, capped at 20)
        conversions = self.conversion_count or 0
        score += min(conversions * 5, 20)

        return min(int(score), 100)
