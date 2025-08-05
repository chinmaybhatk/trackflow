"""
API Authentication for TrackFlow
"""

import frappe
from frappe import _
import jwt
from functools import wraps

def generate_api_key(user=None):
    """
    Generate API key for user
    """
    if not user:
        user = frappe.session.user
    
    # Check if user already has an API key
    existing_key = frappe.db.get_value(
        "TrackFlow API Key",
        {"user": user, "status": "Active"},
        "name"
    )
    
    if existing_key:
        return frappe.get_doc("TrackFlow API Key", existing_key)
    
    # Generate new key
    import secrets
    api_key = secrets.token_urlsafe(32)
    
    # Create API key document
    key_doc = frappe.new_doc("TrackFlow API Key")
    key_doc.user = user
    key_doc.api_key = api_key
    key_doc.status = "Active"
    key_doc.insert()
    
    return key_doc

def validate_api_key(api_key):
    """
    Validate API key and return user
    """
    key_doc = frappe.db.get_value(
        "TrackFlow API Key",
        {"api_key": api_key, "status": "Active"},
        ["user", "usage_count", "last_used"],
        as_dict=True
    )
    
    if not key_doc:
        frappe.throw(_("Invalid API key"), frappe.AuthenticationError)
    
    # Update usage stats
    frappe.db.set_value(
        "TrackFlow API Key",
        {"api_key": api_key},
        {
            "usage_count": (key_doc.usage_count or 0) + 1,
            "last_used": frappe.utils.now_datetime()
        }
    )
    
    return key_doc.user

def require_api_key(f):
    """
    Decorator to require API key authentication
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for API key in headers
        api_key = frappe.get_request_header("X-API-Key")
        
        if not api_key:
            # Check in request params
            api_key = frappe.form_dict.get("api_key")
        
        if not api_key:
            frappe.throw(_("API key required"), frappe.AuthenticationError)
        
        # Validate API key
        user = validate_api_key(api_key)
        
        # Set user context
        frappe.set_user(user)
        
        return f(*args, **kwargs)
    
    return decorated_function

def generate_jwt_token(user, expires_in=3600):
    """
    Generate JWT token for user
    """
    import datetime
    
    payload = {
        "user": user,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in),
        "iat": datetime.datetime.utcnow()
    }
    
    # Get secret from site config
    secret = frappe.local.conf.get("jwt_secret") or frappe.generate_hash()
    
    token = jwt.encode(payload, secret, algorithm="HS256")
    
    return token

def validate_jwt_token(token):
    """
    Validate JWT token and return user
    """
    try:
        # Get secret from site config
        secret = frappe.local.conf.get("jwt_secret") or frappe.generate_hash()
        
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        
        return payload.get("user")
    
    except jwt.ExpiredSignatureError:
        frappe.throw(_("Token has expired"), frappe.AuthenticationError)
    except jwt.InvalidTokenError:
        frappe.throw(_("Invalid token"), frappe.AuthenticationError)