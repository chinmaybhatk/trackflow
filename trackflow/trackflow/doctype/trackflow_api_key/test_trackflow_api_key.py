# -*- coding: utf-8 -*-
# Copyright (c) 2024, TrackFlow and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
import unittest
from datetime import datetime, timedelta

class TestTrackFlowAPIKey(unittest.TestCase):
    def setUp(self):
        # Clean up existing test keys
        frappe.db.delete('TrackFlow API Key', {'key_name': ['like', 'Test %']})
        
    def test_api_key_generation(self):
        # Create API key
        doc = frappe.get_doc({
            'doctype': 'TrackFlow API Key',
            'key_name': 'Test Key 1',
            'permissions': [{
                'permission': 'read_links'
            }],
            'is_active': 1
        })
        doc.insert()
        
        # Check key was generated
        self.assertTrue(doc.api_key)
        self.assertTrue(doc.api_key.startswith('tf_'))
        self.assertTrue(doc.api_key_hash)
        
    def test_permission_validation(self):
        # Test empty permissions
        with self.assertRaises(frappe.ValidationError):
            doc = frappe.get_doc({
                'doctype': 'TrackFlow API Key',
                'key_name': 'Test Key No Perms',
                'permissions': [],
                'is_active': 1
            })
            doc.insert()
            
    def test_rate_limit_validation(self):
        # Test invalid rate limits
        with self.assertRaises(frappe.ValidationError):
            doc = frappe.get_doc({
                'doctype': 'TrackFlow API Key',
                'key_name': 'Test Key Bad Limits',
                'permissions': [{
                    'permission': 'read_links'
                }],
                'rate_limit_per_minute': 100,
                'rate_limit_per_hour': 50,  # Less than per minute
                'is_active': 1
            })
            doc.insert()
            
    def test_api_key_validation(self):
        # Create a key
        doc = frappe.get_doc({
            'doctype': 'TrackFlow API Key',
            'key_name': 'Test Key Validation',
            'permissions': [{
                'permission': 'read_links'
            }],
            'is_active': 1
        })
        doc.insert()
        
        # Test validation
        validated = frappe.get_doc('TrackFlow API Key').validate_api_key(doc.api_key)
        self.assertIsNotNone(validated)
        self.assertEqual(validated.name, doc.name)
        
        # Test invalid key
        invalid = frappe.get_doc('TrackFlow API Key').validate_api_key('invalid_key')
        self.assertIsNone(invalid)
        
    def tearDown(self):
        # Clean up test data
        frappe.db.delete('TrackFlow API Key', {'key_name': ['like', 'Test %']})
        frappe.db.commit()
