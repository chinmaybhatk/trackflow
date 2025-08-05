# -*- coding: utf-8 -*-
# Copyright (c) 2024, chinmaybhatk and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, today, nowdate, add_days
import json

class LinkCampaign(Document):
    def validate(self):
        self.validate_dates()
        self.validate_target_url()
        self.validate_utm_parameters()
        self.validate_variants()
        self.set_utm_campaign()
        self.update_status()
        
    def validate_dates(self):
        """Validate campaign dates"""
        if self.end_date and getdate(self.start_date) > getdate(self.end_date):
            frappe.throw(_("End Date cannot be before Start Date"))
            
    def validate_target_url(self):
        """Validate target URL format"""
        if not self.target_url.startswith(('http://', 'https://')):
            frappe.throw(_("Target URL must start with http:// or https://"))
            
    def validate_utm_parameters(self):
        """Validate UTM parameters"""
        # Remove special characters from UTM parameters
        utm_fields = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content']
        for field in utm_fields:
            if self.get(field):
                # Replace spaces with underscores and remove special chars
                cleaned = frappe.scrub(self.get(field)).replace('-', '_')
                self.set(field, cleaned)
                
    def validate_variants(self):
        """Validate variant weights total 100%"""
        if self.enable_variants and self.variants:
            total_weight = sum([v.weight or 0 for v in self.variants])
            if total_weight != 100:
                frappe.throw(_("Variant weights must total 100% (current: {0}%)").format(total_weight))
                
    def set_utm_campaign(self):
        """Auto-set UTM campaign if not provided"""
        if not self.utm_campaign:
            self.utm_campaign = frappe.scrub(self.campaign_name).replace('-', '_')
            
    def update_status(self):
        """Auto-update status based on dates"""
        if self.status not in ["Paused", "Archived"]:
            if self.end_date and getdate(self.end_date) < getdate(today()):
                self.status = "Completed"
            elif getdate(self.start_date) > getdate(today()):
                self.status = "Draft"
            else:
                self.status = "Active"
                
    def on_update(self):
        """Update campaign statistics"""
        self.update_statistics()
        
    def update_statistics(self):
        """Update campaign statistics from click events"""
        # Get total links
        self.total_links = frappe.db.count('Tracked Link', {
            'campaign': self.name
        })
        
        # Get click statistics
        click_stats = frappe.db.sql("""
            SELECT 
                COUNT(*) as total_clicks,
                COUNT(DISTINCT visitor_id) as unique_visitors
            FROM `tabClick Event`
            WHERE campaign = %s
        """, self.name, as_dict=True)[0]
        
        self.total_clicks = click_stats.total_clicks or 0
        self.unique_visitors = click_stats.unique_visitors or 0
        
        # Get last click date
        last_click = frappe.db.get_value('Click Event', 
            {'campaign': self.name}, 
            'creation', 
            order_by='creation desc'
        )
        self.last_click_date = last_click
        
        # Get conversion data if enabled
        if self.enable_conversion_tracking:
            self.conversion_count = frappe.db.count('Link Conversion', {
                'campaign': self.name
            })
            
            if self.unique_visitors > 0:
                self.conversion_rate = (float(self.conversion_count) / self.unique_visitors) * 100
            else:
                self.conversion_rate = 0
                
        self.db_update()
        
    @frappe.whitelist()
    def get_campaign_report_data(self):
        """Get detailed campaign analytics data"""
        data = {
            'overview': {
                'total_links': self.total_links,
                'total_clicks': self.total_clicks,
                'unique_visitors': self.unique_visitors,
                'conversion_count': self.conversion_count,
                'conversion_rate': self.conversion_rate
            },
            'daily_clicks': [],
            'top_links': [],
            'device_stats': [],
            'location_stats': []
        }
        
        # Daily clicks for last 30 days
        daily_clicks = frappe.db.sql("""
            SELECT 
                DATE(creation) as date,
                COUNT(*) as clicks,
                COUNT(DISTINCT visitor_id) as unique_clicks
            FROM `tabClick Event`
            WHERE campaign = %s 
            AND creation >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            GROUP BY DATE(creation)
            ORDER BY date
        """, self.name, as_dict=True)
        data['daily_clicks'] = daily_clicks
        
        # Top performing links
        top_links = frappe.db.sql("""
            SELECT 
                tl.short_code,
                tl.custom_identifier,
                COUNT(ce.name) as click_count
            FROM `tabTracked Link` tl
            LEFT JOIN `tabClick Event` ce ON ce.tracked_link = tl.name
            WHERE tl.campaign = %s
            GROUP BY tl.name
            ORDER BY click_count DESC
            LIMIT 10
        """, self.name, as_dict=True)
        data['top_links'] = top_links
        
        # Device statistics
        device_stats = frappe.db.sql("""
            SELECT 
                device_type,
                COUNT(*) as count
            FROM `tabClick Event`
            WHERE campaign = %s
            GROUP BY device_type
        """, self.name, as_dict=True)
        data['device_stats'] = device_stats
        
        # Location statistics
        location_stats = frappe.db.sql("""
            SELECT 
                country,
                COUNT(*) as count
            FROM `tabClick Event`
            WHERE campaign = %s
            AND country IS NOT NULL
            GROUP BY country
            ORDER BY count DESC
            LIMIT 10
        """, self.name, as_dict=True)
        data['location_stats'] = location_stats
        
        return data
        
    @frappe.whitelist()
    def duplicate_campaign(self, new_name, copy_links=False):
        """Duplicate campaign with optional link copying"""
        # Create new campaign
        new_campaign = frappe.copy_doc(self)
        new_campaign.campaign_name = new_name
        new_campaign.status = "Draft"
        
        # Reset statistics
        new_campaign.total_links = 0
        new_campaign.total_clicks = 0
        new_campaign.unique_visitors = 0
        new_campaign.conversion_count = 0
        new_campaign.conversion_rate = 0
        new_campaign.last_click_date = None
        
        new_campaign.insert()
        
        # Copy links if requested
        if copy_links:
            links = frappe.get_all('Tracked Link', 
                filters={'campaign': self.name},
                fields=['*']
            )
            
            for link in links:
                new_link = frappe.new_doc('Tracked Link')
                for field in link:
                    if field not in ['name', 'creation', 'modified', 'short_code']:
                        new_link.set(field, link[field])
                new_link.campaign = new_campaign.name
                new_link.insert()
                
        return new_campaign.name
        
    def get_campaign_url(self, custom_params=None):
        """Build complete campaign URL with UTM parameters"""
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        
        # Parse target URL
        parsed = urlparse(self.target_url)
        query_params = parse_qs(parsed.query)
        
        # Add UTM parameters
        utm_params = {
            'utm_source': self.utm_source,
            'utm_medium': self.utm_medium
        }
        
        if self.utm_campaign:
            utm_params['utm_campaign'] = self.utm_campaign
        if self.utm_term:
            utm_params['utm_term'] = self.utm_term
        if self.utm_content:
            utm_params['utm_content'] = self.utm_content
            
        # Add custom parameters
        if custom_params:
            utm_params.update(custom_params)
            
        # Merge with existing query params
        for key, value in utm_params.items():
            query_params[key] = [value]
            
        # Rebuild URL
        new_query = urlencode(query_params, doseq=True)
        final_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment
        ))
        
        return final_url


@frappe.whitelist()
def get_active_campaigns():
    """Get list of active campaigns for selection"""
    return frappe.get_all('Link Campaign',
        filters={'status': 'Active'},
        fields=['name', 'campaign_name', 'campaign_type']
    )


@frappe.whitelist()
def update_campaign_status():
    """Scheduled task to update campaign statuses"""
    # Mark completed campaigns
    completed = frappe.db.sql("""
        UPDATE `tabLink Campaign`
        SET status = 'Completed'
        WHERE status = 'Active'
        AND end_date < CURDATE()
    """)
    
    # Activate campaigns that should start
    activated = frappe.db.sql("""
        UPDATE `tabLink Campaign`
        SET status = 'Active'
        WHERE status = 'Draft'
        AND start_date <= CURDATE()
        AND (end_date IS NULL OR end_date >= CURDATE())
    """)
    
    return {
        'completed': completed,
        'activated': activated
    }
