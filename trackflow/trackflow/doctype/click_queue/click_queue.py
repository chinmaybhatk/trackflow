# -*- coding: utf-8 -*-
# Copyright (c) 2024, chinmaybhatk and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

class ClickQueue(Document):
    def process(self):
        """Process this queue item"""
        if self.processed:
            return
            
        try:
            import json
            click_data = json.loads(self.click_data) if isinstance(self.click_data, str) else self.click_data
            
            # Get tracked link
            tracked_link = frappe.db.get_value('Tracked Link', 
                {'short_code': self.short_code}, 
                ['name', 'campaign', 'status']
            )
            
            if not tracked_link:
                raise Exception(f"Tracked link with short code {self.short_code} not found")
                
            link_name, campaign, status = tracked_link
            
            if status != 'Active':
                raise Exception(f"Tracked link {self.short_code} is not active")
            
            # Create click event
            click_event = frappe.new_doc('Click Event')
            click_event.tracked_link = link_name
            click_event.campaign = campaign
            click_event.visitor_id = self.visitor_id
            
            # Map click data fields
            for field, value in click_data.items():
                if hasattr(click_event, field):
                    setattr(click_event, field, value)
                    
            click_event.insert(ignore_permissions=True)
            
            # Mark as processed
            self.processed = 1
            self.processed_at = now_datetime()
            self.db_update()
            
            return click_event.name
            
        except Exception as e:
            self.retry_count = (self.retry_count or 0) + 1
            self.error_message = str(e)
            self.db_update()
            
            # Log error if max retries exceeded
            if self.retry_count >= 3:
                frappe.log_error(
                    f"Failed to process click queue item {self.name} after {self.retry_count} attempts: {str(e)}",
                    "Click Queue Processing Error"
                )
                
            raise


@frappe.whitelist()
def cleanup_processed_queue(days=7):
    """Clean up old processed queue items"""
    deleted = frappe.db.sql("""
        DELETE FROM `tabClick Queue`
        WHERE processed = 1
        AND processed_at < DATE_SUB(NOW(), INTERVAL %s DAY)
    """, days)
    
    return deleted
