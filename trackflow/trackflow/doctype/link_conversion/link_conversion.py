# -*- coding: utf-8 -*-
# Copyright (c) 2024, chinmaybhatk and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, time_diff_in_seconds

class LinkConversion(Document):
    def before_insert(self):
        if not self.conversion_timestamp:
            self.conversion_timestamp = now_datetime()
        self.calculate_time_to_conversion()
        
    def validate(self):
        self.validate_click_event()
        self.set_attribution_weight()
        
    def validate_click_event(self):
        """Ensure click event exists and matches campaign/link"""
        click = frappe.db.get_value('Click Event', 
            self.click_event, 
            ['tracked_link', 'campaign', 'visitor_id', 'click_timestamp'], 
            as_dict=True
        )
        
        if not click:
            frappe.throw(_("Click Event not found"))
            
        if click.tracked_link != self.tracked_link:
            frappe.throw(_("Tracked Link mismatch with Click Event"))
            
        if click.campaign != self.campaign:
            frappe.throw(_("Campaign mismatch with Click Event"))
            
        if click.visitor_id != self.visitor_id:
            frappe.throw(_("Visitor ID mismatch with Click Event"))
            
        self.click_timestamp = click.click_timestamp
        
    def calculate_time_to_conversion(self):
        """Calculate time between click and conversion"""
        if hasattr(self, 'click_timestamp') and self.click_timestamp:
            self.time_to_conversion = time_diff_in_seconds(
                self.conversion_timestamp, 
                self.click_timestamp
            )
            
    def set_attribution_weight(self):
        """Set attribution weight based on model"""
        if not self.attribution_model:
            # Default to last-click attribution
            self.attribution_weight = 1.0
            return
            
        # Get attribution model settings
        model = frappe.get_doc('Attribution Model', self.attribution_model)
        
        # Calculate weight based on model type
        if model.model_type == 'Last Click':
            self.attribution_weight = 1.0
            
        elif model.model_type == 'First Click':
            # Check if this is the first click for the visitor
            first_click = frappe.db.get_value('Click Event',
                {'visitor_id': self.visitor_id},
                'name',
                order_by='click_timestamp asc'
            )
            self.attribution_weight = 1.0 if first_click == self.click_event else 0.0
            
        elif model.model_type == 'Linear':
            # Equal credit to all touchpoints
            total_clicks = frappe.db.count('Click Event', 
                {'visitor_id': self.visitor_id}
            )
            self.attribution_weight = 1.0 / total_clicks if total_clicks > 0 else 1.0
            
        elif model.model_type == 'Time Decay':
            # More credit to recent touchpoints
            # Implementation depends on specific decay formula
            self.attribution_weight = self.calculate_time_decay_weight()
            
        elif model.model_type == 'Position Based':
            # 40% first, 40% last, 20% middle
            self.attribution_weight = self.calculate_position_based_weight()
            
    def calculate_time_decay_weight(self):
        """Calculate weight based on time decay model"""
        # Get all clicks for this visitor
        clicks = frappe.db.get_all('Click Event',
            filters={'visitor_id': self.visitor_id},
            fields=['name', 'click_timestamp'],
            order_by='click_timestamp asc'
        )
        
        if not clicks:
            return 1.0
            
        # Find position of current click
        current_position = None
        for i, click in enumerate(clicks):
            if click.name == self.click_event:
                current_position = i
                break
                
        if current_position is None:
            return 1.0
            
        # Apply exponential decay
        # More recent clicks get higher weight
        decay_rate = 0.5  # Configurable
        days_from_last = (len(clicks) - current_position - 1)
        weight = pow(decay_rate, days_from_last)
        
        return weight
        
    def calculate_position_based_weight(self):
        """Calculate weight based on position in journey"""
        # Get all clicks for this visitor
        clicks = frappe.db.get_all('Click Event',
            filters={'visitor_id': self.visitor_id},
            fields=['name'],
            order_by='click_timestamp asc'
        )
        
        if not clicks:
            return 1.0
            
        total_clicks = len(clicks)
        
        # Find position of current click
        current_position = None
        for i, click in enumerate(clicks):
            if click.name == self.click_event:
                current_position = i
                break
                
        if current_position is None:
            return 1.0
            
        # Position-based attribution
        if current_position == 0:  # First click
            return 0.4
        elif current_position == total_clicks - 1:  # Last click
            return 0.4
        else:  # Middle clicks
            middle_clicks = total_clicks - 2
            return 0.2 / middle_clicks if middle_clicks > 0 else 0.2
            
    def after_insert(self):
        """Update related documents"""
        # Update click event
        frappe.db.set_value('Click Event', self.click_event, {
            'led_to_conversion': 1,
            'conversion_type': self.conversion_type,
            'conversion_value': self.conversion_value
        })
        
        # Update campaign stats
        campaign = frappe.get_doc('Link Campaign', self.campaign)
        campaign.update_statistics()
        
        # Create notification if enabled
        settings = frappe.get_cached_doc('TrackFlow Settings')
        if settings.enable_conversion_notifications:
            self.create_notification()
            
    def create_notification(self):
        """Create notification for conversion"""
        notification = frappe.new_doc('Notification Log')
        notification.subject = f'New {self.conversion_type} Conversion'
        notification.email_content = f"""
            <h3>New Conversion Recorded</h3>
            <p>Campaign: {self.campaign}</p>
            <p>Type: {self.conversion_type}</p>
            <p>Value: {frappe.format_value(self.conversion_value, {'fieldtype': 'Currency'})}</p>
            <p>Time to Conversion: {frappe.format_value(self.time_to_conversion, {'fieldtype': 'Duration'})}</p>
        """
        notification.for_user = frappe.session.user
        notification.insert(ignore_permissions=True)


@frappe.whitelist()
def get_conversion_analytics(period=30, campaign=None, conversion_type=None):
    """Get conversion analytics data"""
    conditions = []
    if campaign:
        conditions.append(f"campaign = '{campaign}'")
    if conversion_type:
        conditions.append(f"conversion_type = '{conversion_type}'")
        
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    # Get conversion metrics
    data = frappe.db.sql(f"""
        SELECT 
            DATE(conversion_timestamp) as date,
            COUNT(*) as conversions,
            SUM(conversion_value) as total_value,
            AVG(conversion_value) as avg_value,
            AVG(time_to_conversion) as avg_time_to_conversion
        FROM `tabLink Conversion`
        WHERE {where_clause}
        AND conversion_timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
        GROUP BY DATE(conversion_timestamp)
        ORDER BY date
    """, period, as_dict=True)
    
    return data
