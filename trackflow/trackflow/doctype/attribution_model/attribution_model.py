# Copyright (c) 2024, Chinmay Bhat and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime, timedelta
import json


class AttributionModel(Document):
    def validate(self):
        """Validate attribution model settings"""
        # Ensure only one default model
        if self.is_default:
            existing_default = frappe.db.get_value(
                "Attribution Model", 
                {"is_default": 1, "name": ["!=", self.name]}, 
                "name"
            )
            if existing_default:
                frappe.throw(f"Another model '{existing_default}' is already set as default. Please uncheck it first.")
        
        # Validate lookback days
        if self.lookback_days and self.lookback_days < 1:
            frappe.throw("Lookback window must be at least 1 day")
            
        # Validate decay rate for time decay model
        if self.model_type == "time_decay" and self.decay_rate:
            if not (0 < self.decay_rate <= 1):
                frappe.throw("Decay rate must be between 0 and 1")

    def calculate_attribution(self, touchpoints, conversion_value):
        """Calculate attribution for touchpoints based on this model's configuration
        
        Args:
            touchpoints: List of touchpoint dicts with channel, timestamp, etc.
            conversion_value: Total value to distribute
            
        Returns:
            Dict with channel attribution: {channel: {credit: float, value: float}}
        """
        if not touchpoints:
            return {}
            
        # Filter touchpoints by lookback window
        filtered_touchpoints = self._filter_by_lookback(touchpoints)
        
        if not filtered_touchpoints:
            return {}
            
        # Apply minimum touchpoints filter
        if len(filtered_touchpoints) < (self.minimum_touchpoints or 1):
            return {}
            
        # Apply attribution model
        if self.model_type == "first_touch":
            return self._first_touch_attribution(filtered_touchpoints, conversion_value)
        elif self.model_type == "last_touch":
            return self._last_touch_attribution(filtered_touchpoints, conversion_value)
        elif self.model_type == "linear":
            return self._linear_attribution(filtered_touchpoints, conversion_value)
        elif self.model_type == "time_decay":
            return self._time_decay_attribution(filtered_touchpoints, conversion_value)
        elif self.model_type == "position_based":
            return self._position_based_attribution(filtered_touchpoints, conversion_value)
        elif self.model_type == "custom":
            return self._custom_attribution(filtered_touchpoints, conversion_value)
        else:
            # Default to last touch
            return self._last_touch_attribution(filtered_touchpoints, conversion_value)
    
    def _filter_by_lookback(self, touchpoints):
        """Filter touchpoints by lookback window"""
        if not self.lookback_days:
            return touchpoints
            
        cutoff_date = datetime.now() - timedelta(days=self.lookback_days)
        
        filtered = []
        for tp in touchpoints:
            tp_time = tp.get('timestamp')
            if isinstance(tp_time, str):
                tp_time = datetime.fromisoformat(tp_time.replace('Z', '+00:00'))
            elif not isinstance(tp_time, datetime):
                continue
                
            if tp_time >= cutoff_date:
                filtered.append(tp)
                
        return filtered
    
    def _first_touch_attribution(self, touchpoints, value):
        """100% credit to first touchpoint"""
        if not touchpoints:
            return {}
            
        first_touch = touchpoints[0]
        channel = first_touch.get('channel', 'direct')
        
        return {
            channel: {
                'credit': 1.0,
                'value': float(value),
                'touchpoint_count': 1
            }
        }
    
    def _last_touch_attribution(self, touchpoints, value):
        """100% credit to last touchpoint"""
        if not touchpoints:
            return {}
            
        last_touch = touchpoints[-1]
        channel = last_touch.get('channel', 'direct')
        
        return {
            channel: {
                'credit': 1.0,
                'value': float(value),
                'touchpoint_count': 1
            }
        }
    
    def _linear_attribution(self, touchpoints, value):
        """Equal credit to all touchpoints"""
        if not touchpoints:
            return {}
            
        result = {}
        credit_per_touch = 1.0 / len(touchpoints)
        value_per_touch = float(value) / len(touchpoints)
        
        # Group by channel
        for tp in touchpoints:
            channel = tp.get('channel', 'direct')
            
            if channel not in result:
                result[channel] = {
                    'credit': 0.0,
                    'value': 0.0,
                    'touchpoint_count': 0
                }
                
            result[channel]['credit'] += credit_per_touch
            result[channel]['value'] += value_per_touch
            result[channel]['touchpoint_count'] += 1
            
        return result
    
    def _time_decay_attribution(self, touchpoints, value):
        """More credit to recent touchpoints with exponential decay"""
        if not touchpoints:
            return {}
            
        # Get conversion time (last touchpoint time)
        conversion_time = touchpoints[-1].get('timestamp')
        if isinstance(conversion_time, str):
            conversion_time = datetime.fromisoformat(conversion_time.replace('Z', '+00:00'))
            
        # Calculate weights based on decay
        decay_rate = self.decay_rate or 0.1
        weights = []
        
        for tp in touchpoints:
            tp_time = tp.get('timestamp')
            if isinstance(tp_time, str):
                tp_time = datetime.fromisoformat(tp_time.replace('Z', '+00:00'))
                
            days_before = (conversion_time - tp_time).days
            weight = (1 - decay_rate) ** days_before
            weights.append(weight)
            
        total_weight = sum(weights)
        if total_weight == 0:
            return self._linear_attribution(touchpoints, value)
            
        # Distribute credit
        result = {}
        for i, tp in enumerate(touchpoints):
            channel = tp.get('channel', 'direct')
            credit = weights[i] / total_weight
            
            if channel not in result:
                result[channel] = {
                    'credit': 0.0,
                    'value': 0.0,
                    'touchpoint_count': 0
                }
                
            result[channel]['credit'] += credit
            result[channel]['value'] += credit * float(value)
            result[channel]['touchpoint_count'] += 1
            
        return result
    
    def _position_based_attribution(self, touchpoints, value):
        """40% first, 40% last, 20% middle"""
        if not touchpoints:
            return {}
            
        result = {}
        
        if len(touchpoints) == 1:
            # Single touchpoint gets all credit
            channel = touchpoints[0].get('channel', 'direct')
            result[channel] = {
                'credit': 1.0,
                'value': float(value),
                'touchpoint_count': 1
            }
        elif len(touchpoints) == 2:
            # Split 50/50
            for i, tp in enumerate(touchpoints):
                channel = tp.get('channel', 'direct')
                if channel not in result:
                    result[channel] = {'credit': 0.0, 'value': 0.0, 'touchpoint_count': 0}
                    
                result[channel]['credit'] += 0.5
                result[channel]['value'] += 0.5 * float(value)
                result[channel]['touchpoint_count'] += 1
        else:
            # First touch: 40%
            first_channel = touchpoints[0].get('channel', 'direct')
            if first_channel not in result:
                result[first_channel] = {'credit': 0.0, 'value': 0.0, 'touchpoint_count': 0}
            result[first_channel]['credit'] += 0.4
            result[first_channel]['value'] += 0.4 * float(value)
            result[first_channel]['touchpoint_count'] += 1
            
            # Last touch: 40%
            last_channel = touchpoints[-1].get('channel', 'direct')
            if last_channel not in result:
                result[last_channel] = {'credit': 0.0, 'value': 0.0, 'touchpoint_count': 0}
            result[last_channel]['credit'] += 0.4
            result[last_channel]['value'] += 0.4 * float(value)
            result[last_channel]['touchpoint_count'] += 1
            
            # Middle touches: 20% distributed
            middle_count = len(touchpoints) - 2
            if middle_count > 0:
                credit_per_middle = 0.2 / middle_count
                value_per_middle = 0.2 * float(value) / middle_count
                
                for tp in touchpoints[1:-1]:
                    channel = tp.get('channel', 'direct')
                    if channel not in result:
                        result[channel] = {'credit': 0.0, 'value': 0.0, 'touchpoint_count': 0}
                        
                    result[channel]['credit'] += credit_per_middle
                    result[channel]['value'] += value_per_middle
                    result[channel]['touchpoint_count'] += 1
                    
        return result
    
    def _custom_attribution(self, touchpoints, value):
        """Custom attribution based on JSON weights"""
        if not self.custom_weights:
            return self._linear_attribution(touchpoints, value)
            
        try:
            weights_config = json.loads(self.custom_weights)
        except (json.JSONDecodeError, TypeError):
            return self._linear_attribution(touchpoints, value)
            
        # Apply custom logic based on configuration
        # This is a placeholder for custom attribution logic
        return self._linear_attribution(touchpoints, value)


@frappe.whitelist()
def get_default_attribution_model():
    """Get the default attribution model"""
    default_model = frappe.db.get_value(
        "Attribution Model",
        {"is_default": 1, "is_active": 1},
        "name"
    )
    
    if default_model:
        return frappe.get_doc("Attribution Model", default_model)
    
    # Fallback to TrackFlow Settings default
    settings_model = frappe.db.get_single_value(
        "TrackFlow Settings", 
        "default_attribution_model"
    )
    
    if settings_model:
        # Try to find matching model by type
        model = frappe.db.get_value(
            "Attribution Model",
            {"model_type": settings_model.lower().replace(" ", "_"), "is_active": 1},
            "name"
        )
        if model:
            return frappe.get_doc("Attribution Model", model)
    
    # Create basic last touch model if none exists
    return create_default_attribution_models()


def create_default_attribution_models():
    """Create default attribution models"""
    models = [
        {
            "model_name": "Last Touch",
            "model_type": "last_touch",
            "description": "100% credit to the last touchpoint before conversion",
            "is_active": 1,
            "is_default": 1,
            "lookback_days": 30
        },
        {
            "model_name": "First Touch", 
            "model_type": "first_touch",
            "description": "100% credit to the first touchpoint",
            "is_active": 1,
            "lookback_days": 90
        },
        {
            "model_name": "Linear",
            "model_type": "linear", 
            "description": "Equal credit distributed across all touchpoints",
            "is_active": 1,
            "lookback_days": 30
        }
    ]
    
    created_models = []
    for model_data in models:
        if not frappe.db.exists("Attribution Model", {"model_name": model_data["model_name"]}):
            model = frappe.new_doc("Attribution Model")
            model.update(model_data)
            model.insert()
            created_models.append(model)
            
    if created_models:
        frappe.db.commit()
        return created_models[0]  # Return default model
    
    return None
