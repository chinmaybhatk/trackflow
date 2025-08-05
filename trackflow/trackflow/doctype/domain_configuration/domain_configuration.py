# -*- coding: utf-8 -*-
# Copyright (c) 2024, TrackFlow and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import re
from urllib.parse import urlparse

class DomainConfiguration(Document):
    def validate(self):
        self.validate_domain_format()
        self.validate_ssl_certificate()
        self.check_duplicate_domain()
        
    def validate_domain_format(self):
        """Validate domain format"""
        # Remove protocol if present
        domain = self.domain.lower().strip()
        
        # Remove http:// or https://
        domain = re.sub(r'^https?://', '', domain)
        
        # Remove trailing slash
        domain = domain.rstrip('/')
        
        # Basic domain validation
        domain_regex = r'^([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,}$'
        if not re.match(domain_regex, domain):
            frappe.throw(f"Invalid domain format: {domain}")
            
        self.domain = domain
        
    def validate_ssl_certificate(self):
        """Ensure SSL is enabled for security"""
        if not self.use_ssl:
            frappe.msgprint(
                "It's recommended to use SSL for tracking domains to ensure secure data transmission.",
                indicator='orange'
            )
            
    def check_duplicate_domain(self):
        """Check for duplicate domain configurations"""
        existing = frappe.db.exists({
            'doctype': 'Domain Configuration',
            'domain': self.domain,
            'name': ('!=', self.name)
        })
        
        if existing:
            frappe.throw(f"Domain {self.domain} is already configured")
            
    def on_update(self):
        """Clear cache when domain configuration changes"""
        frappe.cache().delete_value('trackflow_domains')
        
    @staticmethod
    def get_active_domains():
        """Get list of active tracking domains"""
        domains = frappe.cache().get_value('trackflow_domains')
        
        if not domains:
            domains = frappe.get_all(
                'Domain Configuration',
                filters={'is_active': 1},
                fields=['domain', 'use_ssl', 'is_default']
            )
            frappe.cache().set_value('trackflow_domains', domains, expires_in_sec=3600)
            
        return domains
        
    @staticmethod
    def get_default_domain():
        """Get the default tracking domain"""
        domains = DomainConfiguration.get_active_domains()
        
        # Find default domain
        for domain in domains:
            if domain.get('is_default'):
                return domain
                
        # Return first active domain if no default
        return domains[0] if domains else None
        
    @staticmethod
    def is_valid_tracking_domain(domain):
        """Check if a domain is configured for tracking"""
        domains = DomainConfiguration.get_active_domains()
        domain_list = [d.get('domain') for d in domains]
        
        # Extract domain from full URL if needed
        parsed = urlparse(domain)
        check_domain = parsed.netloc or domain
        
        return check_domain in domain_list
