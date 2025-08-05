# -*- coding: utf-8 -*-
# Copyright (c) 2024, chinmaybhatk and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import nowdate
import re

class LinkTemplate(Document):
    def validate(self):
        self.validate_url_template()
        self.extract_template_variables()
        
    def validate_url_template(self):
        """Validate URL template format"""
        if not self.url_template:
            frappe.throw(_("URL Template is required"))
            
        # Check for basic URL structure
        if not any(self.url_template.startswith(prefix) for prefix in ['http://', 'https://', '{']):
            frappe.throw(_("URL Template must start with http://, https://, or a variable"))
            
    def extract_template_variables(self):
        """Extract variables from URL template"""
        # Find all {variable_name} patterns
        variables = re.findall(r'\{(\w+)\}', self.url_template)
        
        # Update template variables table
        existing_vars = [v.variable_name for v in self.template_variables]
        
        for var in variables:
            if var not in existing_vars:
                self.append('template_variables', {
                    'variable_name': var,
                    'variable_type': 'Text',
                    'is_required': 1
                })
                
    def apply_template(self, data):
        """Apply data to template and return final URL"""
        url = self.url_template
        
        # Replace all variables
        for var in self.template_variables:
            var_name = var.variable_name
            var_value = data.get(var_name, '')
            
            if var.is_required and not var_value:
                frappe.throw(_("Required variable {0} is missing").format(var_name))
                
            # Apply default value if not provided
            if not var_value and var.default_value:
                var_value = var.default_value
                
            url = url.replace(f'{{{var_name}}}', str(var_value))
            
        return url


@frappe.whitelist()
def create_campaign_from_template(template, campaign_data):
    """Create a new campaign from template"""
    template_doc = frappe.get_doc('Link Template', template)
    campaign_data = frappe.parse_json(campaign_data)
    
    # Prepare template data
    template_data = {
        'campaign_name': campaign_data.get('campaign_name'),
        'date': nowdate(),
        'user': frappe.session.user
    }
    
    # Apply template to get target URL
    target_url = template_doc.apply_template(template_data)
    
    # Create campaign
    campaign = frappe.new_doc('Link Campaign')
    campaign.campaign_name = campaign_data.get('campaign_name')
    campaign.campaign_type = campaign_data.get('campaign_type') or template_doc.default_campaign_type
    campaign.start_date = campaign_data.get('start_date')
    campaign.end_date = campaign_data.get('end_date')
    campaign.target_url = target_url
    campaign.template = template
    
    # Set UTM parameters from template
    campaign.utm_source = template_doc.default_utm_source or 'trackflow'
    campaign.utm_medium = template_doc.default_utm_medium or 'link'
    campaign.utm_campaign = template_doc.default_utm_campaign or frappe.scrub(campaign.campaign_name)
    campaign.utm_term = template_doc.default_utm_term
    campaign.utm_content = template_doc.default_utm_content
    
    campaign.insert()
    
    return campaign.name


@frappe.whitelist()
def get_active_templates():
    """Get list of active templates"""
    return frappe.get_all('Link Template',
        filters={'is_active': 1},
        fields=['name', 'template_name', 'template_type', 'description']
    )
