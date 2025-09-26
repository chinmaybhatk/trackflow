import frappe
from frappe.model.document import Document
import ipaddress


class InternalIpRange(Document):
    def validate(self):
        if not self.ip_range:
            frappe.throw("IP Range is required")
        
        # Validate IP range format
        try:
            ipaddress.ip_network(self.ip_range, strict=False)
        except ValueError:
            frappe.throw(f"Invalid IP range format: {self.ip_range}")
    
    @staticmethod
    def is_internal_ip(ip_address):
        """Check if an IP address is internal based on configured ranges"""
        try:
            ip = ipaddress.ip_address(ip_address)
            
            # Get all internal IP ranges
            internal_ranges = frappe.get_all(
                "Internal IP Range",
                filters={"enabled": 1},
                fields=["ip_range"]
            )
            
            for range_doc in internal_ranges:
                try:
                    network = ipaddress.ip_network(range_doc.ip_range, strict=False)
                    if ip in network:
                        return True
                except ValueError:
                    continue
            
            return False
            
        except ValueError:
            # Invalid IP address
            return False