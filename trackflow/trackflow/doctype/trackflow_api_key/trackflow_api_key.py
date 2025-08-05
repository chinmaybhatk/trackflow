# Copyright (c) 2024, Chinmay Bhat and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import secrets


class TrackFlowAPIKey(Document):
    def before_insert(self):
        """Generate API key before inserting"""
        if not self.api_key:
            self.api_key = self.generate_api_key()
    
    def validate(self):
        """Validate the API key"""
        # Check if key name is unique
        if self.is_new() or self.has_value_changed("key_name"):
            if frappe.db.exists("TrackFlow API Key", {"key_name": self.key_name, "name": ["!=", self.name]}):
                frappe.throw(f"API Key with name '{self.key_name}' already exists")
        
        # Validate expiry date
        if self.expires_on:
            from datetime import datetime
            if isinstance(self.expires_on, str):
                expires_on = datetime.strptime(self.expires_on, "%Y-%m-%d").date()
            else:
                expires_on = self.expires_on
            
            if expires_on < datetime.now().date():
                frappe.throw("Expiry date cannot be in the past")
    
    def generate_api_key(self):
        """Generate a secure API key"""
        # Generate a 32-byte random key and convert to hex
        return f"tf_{secrets.token_hex(32)}"
    
    @frappe.whitelist()
    def regenerate_key(self):
        """Regenerate the API key"""
        self.api_key = self.generate_api_key()
        self.save()
        frappe.msgprint(f"API Key regenerated successfully for {self.key_name}")
        return self.api_key
    
    def is_valid(self):
        """Check if the API key is valid"""
        if not self.is_active:
            return False
        
        if self.expires_on:
            from datetime import datetime
            if isinstance(self.expires_on, str):
                expires_on = datetime.strptime(self.expires_on, "%Y-%m-%d").date()
            else:
                expires_on = self.expires_on
            
            if expires_on < datetime.now().date():
                return False
        
        return True
