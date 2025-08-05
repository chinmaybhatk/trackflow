# -*- coding: utf-8 -*-
# Copyright (c) 2024, TrackFlow and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import json
from datetime import datetime, timedelta

class AttributionModel(Document):
    def validate(self):
        self.validate_model_type()
        self.validate_lookback_window()
        self.validate_weights()
        
    def validate_model_type(self):
        """Validate model type and configuration"""
        valid_types = [
            'first_touch', 'last_touch', 'linear', 
            'time_decay', 'position_based', 'custom'
        ]
        
        if self.model_type not in valid_types:
            frappe.throw(f"Invalid model type: {self.model_type}")
            
    def validate_lookback_window(self):
        """Validate lookback window"""
        if self.lookback_days < 1:
            frappe.throw("Lookback window must be at least 1 day")
            
        if self.lookback_days > 365:
            frappe.throw("Lookback window cannot exceed 365 days")
            
    def validate_weights(self):
        """Validate custom weights if using custom model"""
        if self.model_type == 'custom' and self.custom_weights:
            weights = self.custom_weights
            
            # Total weight for each position type should sum to 100
            if weights.get('first_touch', 0) + weights.get('middle_touches', 0) + \
               weights.get('last_touch', 0) != 100:
                frappe.throw("Custom weights must sum to 100%")
                
    def calculate_attribution(self, touchpoints, conversion_value=None):
        """Calculate attribution for given touchpoints"""
        if not touchpoints:
            return {}
            
        # Filter touchpoints within lookback window
        cutoff_date = datetime.now() - timedelta(days=self.lookback_days)
        valid_touchpoints = [
            tp for tp in touchpoints 
            if tp.get('timestamp') >= cutoff_date
        ]
        
        if not valid_touchpoints:
            return {}
            
        # Sort by timestamp
        valid_touchpoints.sort(key=lambda x: x.get('timestamp'))
        
        # Calculate based on model type
        if self.model_type == 'first_touch':
            return self._first_touch_attribution(valid_touchpoints, conversion_value)
        elif self.model_type == 'last_touch':
            return self._last_touch_attribution(valid_touchpoints, conversion_value)
        elif self.model_type == 'linear':
            return self._linear_attribution(valid_touchpoints, conversion_value)
        elif self.model_type == 'time_decay':
            return self._time_decay_attribution(valid_touchpoints, conversion_value)
        elif self.model_type == 'position_based':
            return self._position_based_attribution(valid_touchpoints, conversion_value)
        elif self.model_type == 'custom':
            return self._custom_attribution(valid_touchpoints, conversion_value)
            
    def _first_touch_attribution(self, touchpoints, value):
        """First touch gets 100% credit"""
        if not touchpoints:
            return {}
            
        first = touchpoints[0]
        return {
            first.get('channel', 'unknown'): {
                'credit': 1.0,
                'value': value or 0,
                'touchpoint_id': first.get('id')
            }
        }
        
    def _last_touch_attribution(self, touchpoints, value):
        """Last touch gets 100% credit"""
        if not touchpoints:
            return {}
            
        last = touchpoints[-1]
        return {
            last.get('channel', 'unknown'): {
                'credit': 1.0,
                'value': value or 0,
                'touchpoint_id': last.get('id')
            }
        }
        
    def _linear_attribution(self, touchpoints, value):
        """Equal credit to all touchpoints"""
        if not touchpoints:
            return {}
            
        credit_per_touch = 1.0 / len(touchpoints)
        attribution = {}
        
        for tp in touchpoints:
            channel = tp.get('channel', 'unknown')
            if channel not in attribution:
                attribution[channel] = {
                    'credit': 0,
                    'value': 0,
                    'touchpoint_ids': []
                }
                
            attribution[channel]['credit'] += credit_per_touch
            attribution[channel]['value'] += (value or 0) * credit_per_touch
            attribution[channel]['touchpoint_ids'].append(tp.get('id'))
            
        return attribution
        
    def _time_decay_attribution(self, touchpoints, value):
        """More recent touchpoints get more credit"""
        if not touchpoints:
            return {}
            
        # Calculate decay factor based on time
        latest_time = touchpoints[-1].get('timestamp')
        decay_rate = self.decay_rate or 0.1
        
        weights = []
        for tp in touchpoints:
            days_before = (latest_time - tp.get('timestamp')).days
            weight = (1 - decay_rate) ** days_before
            weights.append(weight)
            
        # Normalize weights
        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]
        
        # Calculate attribution
        attribution = {}
        for i, tp in enumerate(touchpoints):
            channel = tp.get('channel', 'unknown')
            if channel not in attribution:
                attribution[channel] = {
                    'credit': 0,
                    'value': 0,
                    'touchpoint_ids': []
                }
                
            attribution[channel]['credit'] += normalized_weights[i]
            attribution[channel]['value'] += (value or 0) * normalized_weights[i]
            attribution[channel]['touchpoint_ids'].append(tp.get('id'))
            
        return attribution
        
    def _position_based_attribution(self, touchpoints, value):
        """40% first, 40% last, 20% middle touches"""
        if not touchpoints:
            return {}
            
        attribution = {}
        
        if len(touchpoints) == 1:
            # Single touchpoint gets all credit
            return self._first_touch_attribution(touchpoints, value)
        elif len(touchpoints) == 2:
            # Split 50/50 between first and last
            for i, tp in enumerate(touchpoints):
                channel = tp.get('channel', 'unknown')
                attribution[channel] = {
                    'credit': 0.5,
                    'value': (value or 0) * 0.5,
                    'touchpoint_id': tp.get('id')
                }
        else:
            # Standard position-based: 40% first, 40% last, 20% middle
            middle_count = len(touchpoints) - 2
            middle_credit = 0.2 / middle_count if middle_count > 0 else 0
            
            for i, tp in enumerate(touchpoints):
                channel = tp.get('channel', 'unknown')
                
                if i == 0:  # First touch
                    credit = 0.4
                elif i == len(touchpoints) - 1:  # Last touch
                    credit = 0.4
                else:  # Middle touches
                    credit = middle_credit
                    
                if channel not in attribution:
                    attribution[channel] = {
                        'credit': 0,
                        'value': 0,
                        'touchpoint_ids': []
                    }
                    
                attribution[channel]['credit'] += credit
                attribution[channel]['value'] += (value or 0) * credit
                attribution[channel]['touchpoint_ids'].append(tp.get('id'))
                
        return attribution
        
    def _custom_attribution(self, touchpoints, value):
        """Apply custom weights defined by user"""
        if not touchpoints or not self.custom_weights:
            return {}
            
        weights = json.loads(self.custom_weights) if isinstance(self.custom_weights, str) else self.custom_weights
        
        # Apply custom logic based on weights configuration
        # This is a simplified version - can be extended based on requirements
        attribution = {}
        
        for i, tp in enumerate(touchpoints):
            channel = tp.get('channel', 'unknown')
            
            # Determine position type
            if i == 0:
                position_weight = weights.get('first_touch', 0) / 100
            elif i == len(touchpoints) - 1:
                position_weight = weights.get('last_touch', 0) / 100
            else:
                middle_count = len(touchpoints) - 2
                position_weight = (weights.get('middle_touches', 0) / 100) / middle_count
                
            if channel not in attribution:
                attribution[channel] = {
                    'credit': 0,
                    'value': 0,
                    'touchpoint_ids': []
                }
                
            attribution[channel]['credit'] += position_weight
            attribution[channel]['value'] += (value or 0) * position_weight
            attribution[channel]['touchpoint_ids'].append(tp.get('id'))
            
        return attribution
        
    @staticmethod
    def get_default_model():
        """Get the default attribution model"""
        default = frappe.db.get_value(
            'Attribution Model',
            {'is_default': 1, 'is_active': 1},
            ['name', 'model_type', 'lookback_days'],
            as_dict=True
        )
        
        if not default:
            # Return a basic last-touch model as fallback
            return {
                'name': 'last_touch_default',
                'model_type': 'last_touch',
                'lookback_days': 30
            }
            
        return default
