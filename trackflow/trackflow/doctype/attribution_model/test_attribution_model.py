# -*- coding: utf-8 -*-
# Copyright (c) 2024, TrackFlow and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
import unittest
from datetime import datetime, timedelta

class TestAttributionModel(unittest.TestCase):
    def setUp(self):
        # Clean up existing test models
        frappe.db.delete('Attribution Model', {'model_name': ['like', 'Test %']})
        
    def test_first_touch_attribution(self):
        # Create first touch model
        model = frappe.get_doc({
            'doctype': 'Attribution Model',
            'model_name': 'Test First Touch',
            'model_type': 'first_touch',
            'lookback_days': 30,
            'is_active': 1
        })
        model.insert()
        
        # Test touchpoints
        touchpoints = [
            {'id': '1', 'channel': 'organic', 'timestamp': datetime.now() - timedelta(days=5)},
            {'id': '2', 'channel': 'paid', 'timestamp': datetime.now() - timedelta(days=3)},
            {'id': '3', 'channel': 'email', 'timestamp': datetime.now() - timedelta(days=1)}
        ]
        
        attribution = model.calculate_attribution(touchpoints, 100)
        
        # First touch (organic) should get all credit
        self.assertEqual(attribution['organic']['credit'], 1.0)
        self.assertEqual(attribution['organic']['value'], 100)
        self.assertNotIn('paid', attribution)
        self.assertNotIn('email', attribution)
        
    def test_linear_attribution(self):
        # Create linear model
        model = frappe.get_doc({
            'doctype': 'Attribution Model',
            'model_name': 'Test Linear',
            'model_type': 'linear',
            'lookback_days': 30,
            'is_active': 1
        })
        model.insert()
        
        # Test touchpoints
        touchpoints = [
            {'id': '1', 'channel': 'organic', 'timestamp': datetime.now() - timedelta(days=5)},
            {'id': '2', 'channel': 'paid', 'timestamp': datetime.now() - timedelta(days=3)},
            {'id': '3', 'channel': 'email', 'timestamp': datetime.now() - timedelta(days=1)}
        ]
        
        attribution = model.calculate_attribution(touchpoints, 90)
        
        # Each channel should get equal credit (33.33%)
        self.assertAlmostEqual(attribution['organic']['credit'], 0.333, places=2)
        self.assertAlmostEqual(attribution['paid']['credit'], 0.333, places=2)
        self.assertAlmostEqual(attribution['email']['credit'], 0.333, places=2)
        self.assertAlmostEqual(attribution['organic']['value'], 30, places=0)
        
    def test_lookback_window(self):
        # Create model with 7-day lookback
        model = frappe.get_doc({
            'doctype': 'Attribution Model',
            'model_name': 'Test Lookback',
            'model_type': 'linear',
            'lookback_days': 7,
            'is_active': 1
        })
        model.insert()
        
        # Test touchpoints with some outside lookback window
        touchpoints = [
            {'id': '1', 'channel': 'organic', 'timestamp': datetime.now() - timedelta(days=10)},  # Outside window
            {'id': '2', 'channel': 'paid', 'timestamp': datetime.now() - timedelta(days=5)},     # Inside window
            {'id': '3', 'channel': 'email', 'timestamp': datetime.now() - timedelta(days=1)}     # Inside window
        ]
        
        attribution = model.calculate_attribution(touchpoints, 100)
        
        # Only paid and email should be included
        self.assertNotIn('organic', attribution)
        self.assertIn('paid', attribution)
        self.assertIn('email', attribution)
        self.assertAlmostEqual(attribution['paid']['credit'], 0.5)
        self.assertAlmostEqual(attribution['email']['credit'], 0.5)
        
    def tearDown(self):
        # Clean up test data
        frappe.db.delete('Attribution Model', {'model_name': ['like', 'Test %']})
        frappe.db.commit()
