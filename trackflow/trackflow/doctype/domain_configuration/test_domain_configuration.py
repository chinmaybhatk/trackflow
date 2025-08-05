# -*- coding: utf-8 -*-
# Copyright (c) 2024, TrackFlow and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
import unittest

class TestDomainConfiguration(unittest.TestCase):
    def setUp(self):
        # Clean up existing test domains
        frappe.db.delete('Domain Configuration', {'domain': ['like', 'test-%']})
        
    def test_domain_validation(self):
        # Test valid domain
        doc = frappe.get_doc({
            'doctype': 'Domain Configuration',
            'domain': 'test-link.example.com',
            'is_active': 1
        })
        doc.insert()
        self.assertTrue(doc.name)
        
        # Test invalid domain format
        with self.assertRaises(frappe.ValidationError):
            doc2 = frappe.get_doc({
                'doctype': 'Domain Configuration',
                'domain': 'invalid domain with spaces',
                'is_active': 1
            })
            doc2.insert()
            
    def test_duplicate_domain(self):
        # Create first domain
        doc1 = frappe.get_doc({
            'doctype': 'Domain Configuration',
            'domain': 'test-unique.example.com',
            'is_active': 1
        })
        doc1.insert()
        
        # Try to create duplicate
        with self.assertRaises(frappe.ValidationError):
            doc2 = frappe.get_doc({
                'doctype': 'Domain Configuration',
                'domain': 'test-unique.example.com',
                'is_active': 1
            })
            doc2.insert()
            
    def test_default_domain(self):
        # Create multiple domains
        doc1 = frappe.get_doc({
            'doctype': 'Domain Configuration',
            'domain': 'test-domain1.example.com',
            'is_active': 1,
            'is_default': 0
        })
        doc1.insert()
        
        doc2 = frappe.get_doc({
            'doctype': 'Domain Configuration',
            'domain': 'test-domain2.example.com',
            'is_active': 1,
            'is_default': 1
        })
        doc2.insert()
        
        # Test get_default_domain
        default = frappe.get_doc('Domain Configuration').get_default_domain()
        self.assertEqual(default.get('domain'), 'test-domain2.example.com')
        
    def tearDown(self):
        # Clean up test data
        frappe.db.delete('Domain Configuration', {'domain': ['like', 'test-%']})
        frappe.db.commit()
