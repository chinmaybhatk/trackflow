"""
Attribution calculation module for TrackFlow
"""

import frappe
from frappe import _
import json
from datetime import datetime, timedelta


class AttributionCalculator:
    """Calculate multi-touch attribution for conversions"""
    
    def __init__(self, visitor_id, conversion_value, attribution_model="last_touch"):
        self.visitor_id = visitor_id
        self.conversion_value = conversion_value
        self.attribution_model = attribution_model
        self.touchpoints = []
        
    def calculate(self):
        """Calculate attribution based on selected model"""
        # Get all touchpoints
        self.touchpoints = self.get_touchpoints()
        
        if not self.touchpoints:
            return {"touchpoints": [], "total_credit": 0}
            
        # Apply attribution model
        if self.attribution_model == "last_touch":
            return self.last_touch_attribution()
        elif self.attribution_model == "first_touch":
            return self.first_touch_attribution()
        elif self.attribution_model == "linear":
            return self.linear_attribution()
        elif self.attribution_model == "time_decay":
            return self.time_decay_attribution()
        elif self.attribution_model == "position_based":
            return self.position_based_attribution()
        else:
            # Default to last touch
            return self.last_touch_attribution()
            
    def get_touchpoints(self):
        """Get all touchpoints for the visitor"""
        settings = frappe.get_single("TrackFlow Settings")
        attribution_window = settings.attribution_window_days or 90
        
        # Calculate cutoff date
        cutoff_date = frappe.utils.add_to_date(
            frappe.utils.now(),
            days=-attribution_window
        )
        
        # Get all relevant events
        events = frappe.get_all(
            "Visitor Event",
            filters={
                "visitor": self.visitor_id,
                "timestamp": [">=", cutoff_date],
                "event_type": ["in", ["page_view", "campaign_click", "form_submission"]]
            },
            fields=["event_type", "timestamp", "event_data", "url"],
            order_by="timestamp asc"
        )
        
        # Get visitor info for source attribution
        visitor = frappe.get_doc("Visitor", self.visitor_id)
        
        touchpoints = []
        for event in events:
            event_data = json.loads(event.event_data or "{}")
            
            touchpoint = {
                "timestamp": event.timestamp,
                "type": event.event_type,
                "url": event.url,
                "source": event_data.get("source") or visitor.source,
                "medium": event_data.get("medium") or visitor.medium,
                "campaign": event_data.get("campaign") or visitor.campaign,
                "credit": 0  # Will be calculated by attribution model
            }
            
            touchpoints.append(touchpoint)
            
        return touchpoints
        
    def last_touch_attribution(self):
        """100% credit to the last touchpoint"""
        if not self.touchpoints:
            return {"touchpoints": [], "total_credit": 0}
            
        # Give all credit to last touchpoint
        self.touchpoints[-1]["credit"] = 100
        
        return {
            "touchpoints": self.touchpoints,
            "total_credit": 100,
            "model": "last_touch"
        }
        
    def first_touch_attribution(self):
        """100% credit to the first touchpoint"""
        if not self.touchpoints:
            return {"touchpoints": [], "total_credit": 0}
            
        # Give all credit to first touchpoint
        self.touchpoints[0]["credit"] = 100
        
        return {
            "touchpoints": self.touchpoints,
            "total_credit": 100,
            "model": "first_touch"
        }
        
    def linear_attribution(self):
        """Equal credit to all touchpoints"""
        if not self.touchpoints:
            return {"touchpoints": [], "total_credit": 0}
            
        # Distribute credit equally
        credit_per_touch = 100 / len(self.touchpoints)
        
        for touchpoint in self.touchpoints:
            touchpoint["credit"] = round(credit_per_touch, 2)
            
        return {
            "touchpoints": self.touchpoints,
            "total_credit": 100,
            "model": "linear"
        }
        
    def time_decay_attribution(self):
        """More credit to recent touchpoints"""
        if not self.touchpoints:
            return {"touchpoints": [], "total_credit": 0}
            
        # Calculate time-based weights
        conversion_time = frappe.utils.get_datetime(self.touchpoints[-1]["timestamp"])
        weights = []
        
        for touchpoint in self.touchpoints:
            touch_time = frappe.utils.get_datetime(touchpoint["timestamp"])
            days_before_conversion = (conversion_time - touch_time).days
            
            # Use exponential decay with 7-day half-life
            weight = 2 ** (-days_before_conversion / 7)
            weights.append(weight)
            
        # Normalize weights to sum to 100
        total_weight = sum(weights)
        
        for i, touchpoint in enumerate(self.touchpoints):
            touchpoint["credit"] = round((weights[i] / total_weight) * 100, 2)
            
        return {
            "touchpoints": self.touchpoints,
            "total_credit": 100,
            "model": "time_decay"
        }
        
    def position_based_attribution(self):
        """40% first, 40% last, 20% middle touchpoints"""
        if not self.touchpoints:
            return {"touchpoints": [], "total_credit": 0}
            
        if len(self.touchpoints) == 1:
            # Only one touchpoint gets all credit
            self.touchpoints[0]["credit"] = 100
        elif len(self.touchpoints) == 2:
            # Split 50/50 between first and last
            self.touchpoints[0]["credit"] = 50
            self.touchpoints[1]["credit"] = 50
        else:
            # 40% first, 40% last, 20% distributed among middle
            self.touchpoints[0]["credit"] = 40
            self.touchpoints[-1]["credit"] = 40
            
            middle_count = len(self.touchpoints) - 2
            middle_credit = 20 / middle_count
            
            for i in range(1, len(self.touchpoints) - 1):
                self.touchpoints[i]["credit"] = round(middle_credit, 2)
                
        return {
            "touchpoints": self.touchpoints,
            "total_credit": 100,
            "model": "position_based"
        }


def get_attribution_summary(deal_name):
    """Get attribution summary for a deal"""
    deal = frappe.get_doc("CRM Deal", deal_name)
    
    if not deal.trackflow_attribution_data:
        return None
        
    attribution_data = json.loads(deal.trackflow_attribution_data)
    
    # Summarize by source
    source_summary = {}
    for touchpoint in attribution_data.get("touchpoints", []):
        source = touchpoint.get("source", "direct")
        credit = touchpoint.get("credit", 0)
        
        if source in source_summary:
            source_summary[source] += credit
        else:
            source_summary[source] = credit
            
    # Summarize by campaign
    campaign_summary = {}
    for touchpoint in attribution_data.get("touchpoints", []):
        campaign = touchpoint.get("campaign")
        if campaign:
            credit = touchpoint.get("credit", 0)
            
            if campaign in campaign_summary:
                campaign_summary[campaign] += credit
            else:
                campaign_summary[campaign] = credit
                
    return {
        "model": attribution_data.get("model"),
        "touchpoint_count": len(attribution_data.get("touchpoints", [])),
        "source_summary": source_summary,
        "campaign_summary": campaign_summary,
        "deal_value": deal.annual_revenue
    }
