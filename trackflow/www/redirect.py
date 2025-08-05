# -*- coding: utf-8 -*-
# Copyright (c) 2024, chinmaybhatk and contributors
# For license information, please see license.txt

import frappe
from frappe import _
import json
from werkzeug.wrappers import Response
from werkzeug.exceptions import NotFound
from urllib.parse import urlparse
import hashlib
from frappe.utils import cint

def get_context(context):
    """This won't be used as we're handling redirects directly"""
    pass

def handle_redirect(path_parts):
    """Handle redirect for tracking links"""
    if len(path_parts) < 2 or path_parts[0] != 'redirect':
        return None
        
    short_code = path_parts[1]
    
    # Check if link exists and is active
    link = frappe.db.get_value('Tracked Link', 
        {'short_code': short_code}, 
        ['name', 'status', 'target_url', 'campaign'], 
        as_dict=True
    )
    
    if not link or link.status != 'Active':
        # Return 404 for invalid or inactive links
        raise NotFound
        
    # Get visitor data
    visitor_data = get_visitor_data()
    
    # Check if we should use queue for high volume
    settings = frappe.get_cached_doc('TrackFlow Settings')
    use_queue = settings.use_queue_for_clicks
    
    if use_queue:
        # Add to queue for async processing
        queue_item = frappe.new_doc('Click Queue')
        queue_item.short_code = short_code
        queue_item.visitor_id = visitor_data['visitor_id']
        queue_item.click_data = json.dumps(visitor_data)
        queue_item.insert(ignore_permissions=True)
        frappe.db.commit()
    else:
        # Process click immediately
        try:
            tracked_link = frappe.get_doc('Tracked Link', link.name)
            tracked_link.record_click(visitor_data)
            frappe.db.commit()
        except Exception as e:
            # Log error but don't stop redirect
            frappe.log_error(f"Error recording click for {short_code}: {str(e)}")
    
    # Get final redirect URL
    tracked_link = frappe.get_doc('Tracked Link', link.name)
    redirect_url = tracked_link.get_final_url(visitor_data)
    
    # Create redirect response
    response = Response()
    response.status_code = 302
    response.location = redirect_url
    
    # Set cache headers to prevent caching
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response

def get_visitor_data():
    """Extract visitor data from request"""
    request = frappe.request
    
    # Generate visitor ID
    visitor_id = get_visitor_id()
    
    # Get IP address
    ip_address = get_client_ip()
    
    # Parse user agent
    user_agent = request.headers.get('User-Agent', '')
    
    # Get referrer
    referrer = request.headers.get('Referer', '')
    
    # Get query parameters
    query_params = dict(request.args)
    
    # Get location data (if enabled)
    location_data = get_location_from_ip(ip_address) if frappe.get_cached_doc('TrackFlow Settings').enable_geo_tracking else {}
    
    visitor_data = {
        'visitor_id': visitor_id,
        'ip_address': ip_address,
        'user_agent': user_agent,
        'referrer': referrer,
        'query_parameters': json.dumps(query_params),
        'session_id': frappe.session.sid if frappe.session else None,
        **location_data
    }
    
    return visitor_data

def get_visitor_id():
    """Generate or retrieve visitor ID"""
    # Try to get from cookie first
    visitor_id = frappe.request.cookies.get('tf_visitor_id')
    
    if not visitor_id:
        # Generate new visitor ID
        # Use combination of IP, user agent, and timestamp
        data = f"{get_client_ip()}{frappe.request.headers.get('User-Agent', '')}{frappe.utils.now()}"
        visitor_id = hashlib.md5(data.encode()).hexdigest()
        
        # Set cookie for future visits
        frappe.local.cookie_manager.set_cookie('tf_visitor_id', visitor_id, max_age=365*24*60*60)
    
    return visitor_id

def get_client_ip():
    """Get client IP address, considering proxies"""
    request = frappe.request
    
    # Check for proxy headers
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        # Get the first IP in the chain
        return forwarded_for.split(',')[0].strip()
    
    # Check other proxy headers
    real_ip = request.headers.get('X-Real-IP')
    if real_ip:
        return real_ip
    
    # Fall back to remote_addr
    return request.remote_addr or '0.0.0.0'

def get_location_from_ip(ip_address):
    """Get location data from IP address"""
    location_data = {}
    
    try:
        # Check if we have a geo IP service configured
        settings = frappe.get_cached_doc('TrackFlow Settings')
        
        if settings.geo_ip_service == 'ipapi':
            # Use ip-api.com (free tier available)
            import requests
            response = requests.get(f'http://ip-api.com/json/{ip_address}', timeout=2)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    location_data = {
                        'country': data.get('country'),
                        'country_code': data.get('countryCode'),
                        'region': data.get('regionName'),
                        'city': data.get('city'),
                        'latitude': data.get('lat'),
                        'longitude': data.get('lon'),
                        'timezone': data.get('timezone'),
                        'isp': data.get('isp')
                    }
                    
    except Exception as e:
        # Log error but don't stop the redirect
        frappe.log_error(f"Error getting location for IP {ip_address}: {str(e)}")
    
    return location_data

# Hook into Frappe's request handling
def handle_request():
    """Hook to handle redirect requests"""
    path = frappe.request.path.strip('/')
    path_parts = path.split('/')
    
    if path_parts[0] == 'redirect':
        return handle_redirect(path_parts)
    
    return None
