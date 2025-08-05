# -*- coding: utf-8 -*-
# Copyright (c) 2024, chinmaybhatk and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime
import json
from user_agents import parse as parse_user_agent

class ClickEvent(Document):
    def before_insert(self):
        self.click_timestamp = self.click_timestamp or now_datetime()
        self.parse_user_agent()
        self.set_utm_from_campaign()
        
    def validate(self):
        self.validate_tracked_link()
        
    def validate_tracked_link(self):
        """Ensure tracked link belongs to the campaign"""
        link_campaign = frappe.db.get_value('Tracked Link', self.tracked_link, 'campaign')
        if link_campaign != self.campaign:
            frappe.throw(_("Tracked Link does not belong to the selected Campaign"))
            
    def parse_user_agent(self):
        """Parse user agent string to extract device info"""
        if self.user_agent:
            try:
                ua = parse_user_agent(self.user_agent)
                
                # Device type
                if ua.is_mobile:
                    self.device_type = 'Mobile'
                elif ua.is_tablet:
                    self.device_type = 'Tablet'
                elif ua.is_bot:
                    self.device_type = 'Bot'
                elif ua.is_pc:
                    self.device_type = 'Desktop'
                else:
                    self.device_type = 'Unknown'
                    
                # Browser info
                self.browser = f"{ua.browser.family} {ua.browser.version_string}"
                
                # OS info
                self.os = f"{ua.os.family} {ua.os.version_string}"
                
            except Exception:
                # Fallback if parsing fails
                self.device_type = 'Unknown'
                
    def set_utm_from_campaign(self):
        """Set UTM parameters from campaign if not already set"""
        if not any([self.utm_source, self.utm_medium, self.utm_campaign]):
            campaign = frappe.get_cached_doc('Link Campaign', self.campaign)
            self.utm_source = campaign.utm_source
            self.utm_medium = campaign.utm_medium
            self.utm_campaign = campaign.utm_campaign
            self.utm_term = campaign.utm_term
            self.utm_content = campaign.utm_content
            
    def after_insert(self):
        """Update link and campaign statistics"""
        # Update tracked link stats
        link = frappe.get_doc('Tracked Link', self.tracked_link)
        link.click_count = (link.click_count or 0) + 1
        link.last_clicked = self.click_timestamp
        
        # Check if new unique visitor
        is_unique = not frappe.db.exists('Click Event', {
            'tracked_link': self.tracked_link,
            'visitor_id': self.visitor_id,
            'name': ['!=', self.name]
        })
        
        if is_unique:
            link.unique_visitors = (link.unique_visitors or 0) + 1
            
        link.db_update()
        
        # Update campaign stats
        campaign = frappe.get_doc('Link Campaign', self.campaign)
        campaign.update_statistics()
        
    @frappe.whitelist()
    def mark_as_conversion(self, conversion_type=None, conversion_value=0):
        """Mark this click as leading to a conversion"""
        self.led_to_conversion = 1
        self.conversion_type = conversion_type
        self.conversion_value = conversion_value
        
        # Calculate time to conversion
        if self.click_timestamp:
            time_diff = now_datetime() - self.click_timestamp
            self.time_to_conversion = time_diff.total_seconds()
            
        self.save()
        
        # Create conversion record
        conversion = frappe.new_doc('Link Conversion')
        conversion.click_event = self.name
        conversion.tracked_link = self.tracked_link
        conversion.campaign = self.campaign
        conversion.visitor_id = self.visitor_id
        conversion.conversion_type = conversion_type
        conversion.conversion_value = conversion_value
        conversion.insert()
        
        return conversion.name


@frappe.whitelist()
def get_visitor_journey(visitor_id, limit=50):
    """Get complete journey of a visitor across all campaigns"""
    events = frappe.db.sql("""
        SELECT 
            ce.name,
            ce.click_timestamp,
            ce.tracked_link,
            tl.short_code,
            tl.custom_identifier,
            ce.campaign,
            lc.campaign_name,
            ce.referrer,
            ce.landing_page,
            ce.led_to_conversion,
            ce.conversion_type,
            ce.conversion_value
        FROM `tabClick Event` ce
        JOIN `tabTracked Link` tl ON tl.name = ce.tracked_link
        JOIN `tabLink Campaign` lc ON lc.name = ce.campaign
        WHERE ce.visitor_id = %s
        ORDER BY ce.click_timestamp DESC
        LIMIT %s
    """, (visitor_id, limit), as_dict=True)
    
    return events


@frappe.whitelist()
def get_click_heatmap_data(campaign=None, days=7):
    """Get click data for heatmap visualization"""
    conditions = ""
    if campaign:
        conditions = f"AND campaign = '{campaign}'"
        
    data = frappe.db.sql(f"""
        SELECT 
            DAYOFWEEK(click_timestamp) as day_of_week,
            HOUR(click_timestamp) as hour,
            COUNT(*) as clicks
        FROM `tabClick Event`
        WHERE click_timestamp >= DATE_SUB(NOW(), INTERVAL {days} DAY)
        {conditions}
        GROUP BY DAYOFWEEK(click_timestamp), HOUR(click_timestamp)
    """, as_dict=True)
    
    # Format for heatmap
    heatmap_data = {}
    for row in data:
        key = f"{row.day_of_week}-{row.hour}"
        heatmap_data[key] = row.clicks
        
    return heatmap_data


@frappe.whitelist()
def process_click_queue():
    """Process clicks from queue (for high-volume scenarios)"""
    # Get unprocessed clicks from queue
    queue_items = frappe.get_all('Click Queue',
        filters={'processed': 0},
        fields=['*'],
        limit=100,
        order_by='creation'
    )
    
    processed = 0
    for item in queue_items:
        try:
            # Create click event
            click_data = json.loads(item.click_data)
            click_event = frappe.new_doc('Click Event')
            
            for key, value in click_data.items():
                if hasattr(click_event, key):
                    setattr(click_event, key, value)
                    
            click_event.insert(ignore_permissions=True)
            
            # Mark as processed
            frappe.db.set_value('Click Queue', item.name, 'processed', 1)
            processed += 1
            
        except Exception as e:
            frappe.log_error(f"Error processing click queue item {item.name}: {str(e)}")
            
    frappe.db.commit()
    
    return {'processed': processed, 'remaining': len(queue_items) - processed}
