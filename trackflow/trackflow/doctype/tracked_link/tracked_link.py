# -*- coding: utf-8 -*-
# Copyright (c) 2024, chinmaybhatk and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, now_datetime
import string
import random
import json
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

class TrackedLink(Document):
    def before_insert(self):
        self.generate_short_code()
        self.set_created_by()
        
    def validate(self):
        self.validate_campaign()
        self.validate_target_url()
        self.validate_expiry()
        self.update_status()
        
    def generate_short_code(self):
        """Generate unique short code"""
        if not self.short_code:
            settings = frappe.get_cached_doc('TrackFlow Settings')
            length = cint(settings.short_code_length) or 6
            
            # Generate until we find a unique one
            max_attempts = 10
            for _ in range(max_attempts):
                code = self.generate_random_code(length)
                if not frappe.db.exists('Tracked Link', code):
                    self.short_code = code
                    break
            else:
                frappe.throw(_("Could not generate unique short code. Please try again."))
                
    def generate_random_code(self, length):
        """Generate random alphanumeric code"""
        chars = string.ascii_letters + string.digits
        # Remove confusing characters
        chars = chars.replace('0', '').replace('O', '').replace('l', '').replace('I', '')
        return ''.join(random.choice(chars) for _ in range(length))
        
    def set_created_by(self):
        """Set the user who created this link"""
        if not self.created_by_user:
            self.created_by_user = frappe.session.user
            
    def validate_campaign(self):
        """Validate campaign is active"""
        campaign = frappe.get_doc('Link Campaign', self.campaign)
        if campaign.status not in ['Active', 'Draft']:
            frappe.throw(_("Cannot create links for {0} campaign").format(campaign.status))
            
    def validate_target_url(self):
        """Validate target URL if overridden"""
        if self.target_url and not self.target_url.startswith(('http://', 'https://')):
            frappe.throw(_("Target URL must start with http:// or https://"))
            
    def validate_expiry(self):
        """Check if link has expired"""
        if self.expiry_date and self.expiry_date < now_datetime():
            self.status = 'Expired'
            
    def update_status(self):
        """Update link status based on expiry"""
        if self.status == 'Active' and self.expiry_date and self.expiry_date < now_datetime():
            self.status = 'Expired'
            
    def on_update(self):
        """Update campaign statistics"""
        frappe.get_doc('Link Campaign', self.campaign).update_statistics()
        
    def get_final_url(self, visitor_data=None):
        """Build final URL with all parameters"""
        # Get base URL from override or campaign
        if self.target_url:
            base_url = self.target_url
        else:
            campaign = frappe.get_cached_doc('Link Campaign', self.campaign)
            base_url = campaign.target_url
            
        # Parse URL
        parsed = urlparse(base_url)
        query_params = parse_qs(parsed.query)
        
        # Get UTM parameters from campaign
        campaign = frappe.get_cached_doc('Link Campaign', self.campaign)
        utm_params = {
            'utm_source': campaign.utm_source,
            'utm_medium': campaign.utm_medium
        }
        
        if campaign.utm_campaign:
            utm_params['utm_campaign'] = campaign.utm_campaign
        if campaign.utm_term:
            utm_params['utm_term'] = campaign.utm_term
        if campaign.utm_content:
            utm_params['utm_content'] = campaign.utm_content
            
        # Apply UTM overrides if any
        if self.utm_override:
            try:
                overrides = json.loads(self.utm_override)
                utm_params.update(overrides)
            except:
                pass
                
        # Add TrackFlow tracking parameters
        utm_params['tf_link'] = self.short_code
        utm_params['tf_campaign'] = self.campaign
        
        # Add visitor data if available
        if visitor_data:
            if visitor_data.get('source'):
                utm_params['tf_source'] = visitor_data['source']
            if visitor_data.get('referrer'):
                utm_params['tf_ref'] = visitor_data['referrer'][:100]  # Limit length
                
        # Handle A/B testing variants
        if campaign.enable_variants and campaign.variants:
            variant = self.select_variant(campaign.variants)
            if variant:
                utm_params['tf_variant'] = variant.variant_name
                if variant.utm_content:
                    utm_params['utm_content'] = variant.utm_content
                if variant.target_url:
                    base_url = variant.target_url
                    
        # Merge parameters
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
        
    def select_variant(self, variants):
        """Select variant based on weights"""
        total_weight = sum([v.weight for v in variants])
        rand = random.uniform(0, total_weight)
        
        cumulative = 0
        for variant in variants:
            cumulative += variant.weight
            if rand <= cumulative:
                return variant
                
        return variants[-1] if variants else None
        
    def record_click(self, visitor_data):
        """Record a click event"""
        # Update click statistics
        self.click_count = (self.click_count or 0) + 1
        self.last_clicked = now_datetime()
        
        # Update unique visitors
        visitor_id = visitor_data.get('visitor_id')
        if visitor_id:
            existing_click = frappe.db.exists('Click Event', {
                'tracked_link': self.name,
                'visitor_id': visitor_id
            })
            
            if not existing_click:
                self.unique_visitors = (self.unique_visitors or 0) + 1
                
        self.db_update()
        
        # Create click event record
        click_event = frappe.new_doc('Click Event')
        click_event.tracked_link = self.name
        click_event.campaign = self.campaign
        click_event.visitor_id = visitor_id
        click_event.ip_address = visitor_data.get('ip_address')
        click_event.user_agent = visitor_data.get('user_agent')
        click_event.referrer = visitor_data.get('referrer')
        click_event.device_type = visitor_data.get('device_type')
        click_event.browser = visitor_data.get('browser')
        click_event.os = visitor_data.get('os')
        click_event.country = visitor_data.get('country')
        click_event.city = visitor_data.get('city')
        click_event.insert(ignore_permissions=True)
        
        return click_event.name


@frappe.whitelist()
def create_tracking_link(campaign, custom_identifier=None, target_url=None, 
                        tags=None, expiry_date=None, utm_override=None, notes=None):
    """Create a new tracking link"""
    link = frappe.new_doc('Tracked Link')
    link.campaign = campaign
    link.custom_identifier = custom_identifier
    link.target_url = target_url
    link.tags = tags
    link.expiry_date = expiry_date
    link.utm_override = utm_override
    link.notes = notes
    link.insert()
    
    return {
        'name': link.name,
        'short_code': link.short_code,
        'tracking_url': get_tracking_url(link.short_code)
    }
    

@frappe.whitelist()
def bulk_create_links(campaign, count, custom_identifiers=None, tags=None):
    """Bulk create tracking links"""
    count = cint(count)
    if count > 1000:
        frappe.throw(_("Cannot create more than 1000 links at once"))
        
    identifiers = []
    if custom_identifiers:
        identifiers = [i.strip() for i in custom_identifiers.split(',') if i.strip()]
        
    created_links = []
    
    for i in range(count):
        identifier = identifiers[i] if i < len(identifiers) else None
        
        link = frappe.new_doc('Tracked Link')
        link.campaign = campaign
        link.custom_identifier = identifier
        link.tags = tags
        link.insert()
        
        created_links.append({
            'name': link.name,
            'short_code': link.short_code,
            'custom_identifier': link.custom_identifier,
            'tracking_url': get_tracking_url(link.short_code)
        })
        
    return {
        'count': len(created_links),
        'links': created_links
    }
    

def get_tracking_url(short_code):
    """Get full tracking URL for a short code"""
    settings = frappe.get_cached_doc('TrackFlow Settings')
    base_url = settings.redirect_domain or frappe.utils.get_url()
    return f"{base_url}/redirect/{short_code}"


@frappe.whitelist()
def get_link_analytics(link_name, period='30'):
    """Get detailed analytics for a link"""
    period_days = cint(period)
    
    # Get click data
    clicks = frappe.db.sql("""
        SELECT 
            DATE(creation) as date,
            COUNT(*) as clicks,
            COUNT(DISTINCT visitor_id) as unique_clicks
        FROM `tabClick Event`
        WHERE tracked_link = %s
        AND creation >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
        GROUP BY DATE(creation)
        ORDER BY date
    """, (link_name, period_days), as_dict=True)
    
    # Get device breakdown
    devices = frappe.db.sql("""
        SELECT 
            device_type,
            COUNT(*) as count
        FROM `tabClick Event`
        WHERE tracked_link = %s
        GROUP BY device_type
    """, link_name, as_dict=True)
    
    # Get location data
    locations = frappe.db.sql("""
        SELECT 
            country,
            COUNT(*) as count
        FROM `tabClick Event`
        WHERE tracked_link = %s
        AND country IS NOT NULL
        GROUP BY country
        ORDER BY count DESC
        LIMIT 10
    """, link_name, as_dict=True)
    
    # Get referrer data
    referrers = frappe.db.sql("""
        SELECT 
            referrer,
            COUNT(*) as count
        FROM `tabClick Event`
        WHERE tracked_link = %s
        AND referrer IS NOT NULL
        AND referrer != ''
        GROUP BY referrer
        ORDER BY count DESC
        LIMIT 10
    """, link_name, as_dict=True)
    
    return {
        'clicks': clicks,
        'devices': devices,
        'locations': locations,
        'referrers': referrers
    }


@frappe.whitelist()
def deactivate_expired_links():
    """Scheduled task to deactivate expired links"""
    expired_count = frappe.db.sql("""
        UPDATE `tabTracked Link`
        SET status = 'Expired'
        WHERE status = 'Active'
        AND expiry_date < NOW()
    """)
    
    return expired_count
