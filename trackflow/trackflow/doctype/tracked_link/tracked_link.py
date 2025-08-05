# Copyright (c) 2024, Chinmay Bhat and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import string
import random


class TrackedLink(Document):
    def before_insert(self):
        if not self.short_code:
            self.short_code = self.generate_short_code()
    
    def generate_short_code(self, length=6):
        """Generate a unique short code for the link"""
        chars = string.ascii_letters + string.digits
        while True:
            code = ''.join(random.choice(chars) for _ in range(length))
            if not frappe.db.exists("Tracked Link", {"short_code": code}):
                return code
