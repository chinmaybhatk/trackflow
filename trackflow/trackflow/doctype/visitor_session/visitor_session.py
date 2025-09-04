# -*- coding: utf-8 -*-
# Copyright (c) 2024, TrackFlow and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json
from datetime import datetime, timedelta

class VisitorSession(Document):
    def autoname(self):
        """Set name as visitor_id-timestamp"""
        if self.visitor_id:
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            self.name = f"{self.visitor_id}-{timestamp}"
    
    def validate(self):
        """Validate visitor session data"""
        # Set session start if not set
        if not self.session_start:
            self.session_start = frappe.utils.now_datetime()
        
        # Calculate session duration
        if self.session_end:
            duration = frappe.utils.time_diff_in_seconds(
                self.session_end, self.session_start
            )
            self.duration_seconds = duration
        
        # Parse and validate UTM parameters
        if self.landing_page:
            self.extract_utm_params()
        
        # Set device type
        if self.user_agent:
            self.detect_device_type()
    
    def extract_utm_params(self):
        """Extract UTM parameters from landing page URL"""
        from urllib.parse import urlparse, parse_qs
        
        try:
            parsed = urlparse(self.landing_page)
            params = parse_qs(parsed.query)
            
            self.utm_source = params.get('utm_source', [None])[0]
            self.utm_medium = params.get('utm_medium', [None])[0]
            self.utm_campaign = params.get('utm_campaign', [None])[0]
            self.utm_term = params.get('utm_term', [None])[0]
            self.utm_content = params.get('utm_content', [None])[0]
        except:
            pass
    
    def detect_device_type(self):
        """Detect device type from user agent"""
        ua_lower = (self.user_agent or '').lower()
        
        if 'mobile' in ua_lower or 'android' in ua_lower:
            self.device_type = 'Mobile'
        elif 'tablet' in ua_lower or 'ipad' in ua_lower:
            self.device_type = 'Tablet'
        else:
            self.device_type = 'Desktop'
    
    def on_update(self):
        """Update visitor engagement score"""
        if self.visitor_id:
            self.update_visitor_engagement()
    
    def update_visitor_engagement(self):
        """Calculate and update visitor engagement score"""
        # Get all sessions for this visitor
        sessions = frappe.get_all(
            'Visitor Session',
            filters={'visitor_id': self.visitor_id},
            fields=['duration_seconds', 'page_views', 'events_triggered']
        )
        
        # Calculate engagement score
        total_duration = sum(s.get('duration_seconds', 0) for s in sessions)
        total_pages = sum(s.get('page_views', 0) for s in sessions)
        total_events = sum(s.get('events_triggered', 0) for s in sessions)
        
        engagement_score = (
            (total_duration / 60) * 0.3 +  # Minutes * 0.3
            total_pages * 2 +               # Page views * 2
            total_events * 5                # Events * 5
        )
        
        # Update visitor record if exists
        if frappe.db.exists('Visitor', self.visitor_id):
            frappe.db.set_value(
                'Visitor', 
                self.visitor_id, 
                'engagement_score', 
                engagement_score
            )

@frappe.whitelist()
def get_active_sessions(hours=24):
    """Get active visitor sessions in the last N hours"""
    from_date = datetime.now() - timedelta(hours=hours)
    
    return frappe.get_all(
        'Visitor Session',
        filters={
            'session_start': ['>', from_date]
        },
        fields=['name', 'visitor_id', 'session_start', 'landing_page', 
                'utm_source', 'utm_campaign', 'device_type'],
        order_by='session_start desc'
    )

@frappe.whitelist()
def end_session(session_id):
    """End a visitor session"""
    session = frappe.get_doc('Visitor Session', session_id)
    session.session_end = frappe.utils.now_datetime()
    session.save(ignore_permissions=True)
    return session.name
