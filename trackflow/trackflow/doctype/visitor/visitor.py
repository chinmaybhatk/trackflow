# Copyright (c) 2024, Chinmay Bhat and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Visitor(Document):
    def before_save(self):
        # Update engagement score
        self.engagement_score = self.calculate_engagement_score()
        
    def calculate_engagement_score(self):
        """Calculate visitor engagement based on activities"""
        score = 0
        
        # Clicks (1 point per click, max 20)
        clicks = frappe.db.count("Click Event", {"visitor_id": self.visitor_id})
        score += min(clicks, 20)
        
        # Has lead (20 points)
        if self.lead:
            score += 20
            
        # Has deal (30 points)  
        if self.deal:
            score += 30
            
        # Has organization (10 points)
        if self.organization:
            score += 10
            
        # Page views (0.5 per view, max 10)
        score += min(self.total_page_views * 0.5, 10) if self.total_page_views else 0
        
        # Sessions (2 per session, max 10)
        score += min(self.total_sessions * 2, 10) if self.total_sessions else 0
        
        return min(int(score), 100)
