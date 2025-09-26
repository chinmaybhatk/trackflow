import frappe
from frappe import _
import functools
import traceback

class TrackFlowError(Exception):
    """Base exception for TrackFlow errors"""
    def __init__(self, message, error_code=None, details=None):
        self.message = message
        self.error_code = error_code
        self.details = details
        super().__init__(self.message)

class ValidationError(TrackFlowError):
    """Raised when validation fails"""
    pass

class ConfigurationError(TrackFlowError):
    """Raised when configuration is missing or invalid"""
    pass

class TrackingError(TrackFlowError):
    """Raised when tracking operations fail"""
    pass

class IntegrationError(TrackFlowError):
    """Raised when external integration fails"""
    pass

def handle_error(error_type="general", log_traceback=True, return_response=True):
    """Decorator for consistent error handling
    
    Args:
        error_type: Type of error for logging purposes
        log_traceback: Whether to log full traceback
        return_response: Whether to return error response dict
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except TrackFlowError as e:
                # Handle our custom errors
                if log_traceback:
                    frappe.log_error(
                        f"TrackFlow {error_type} Error: {str(e)}\n{traceback.format_exc()}",
                        f"TrackFlow {e.__class__.__name__}"
                    )
                
                if return_response:
                    return {
                        "status": "error",
                        "error_code": e.error_code or e.__class__.__name__,
                        "message": str(e),
                        "details": e.details
                    }
                else:
                    raise
                    
            except frappe.ValidationError as e:
                # Handle Frappe validation errors
                if log_traceback:
                    frappe.log_error(
                        f"TrackFlow Validation Error: {str(e)}",
                        f"TrackFlow {error_type} Validation Error"
                    )
                
                if return_response:
                    return {
                        "status": "error",
                        "error_code": "VALIDATION_ERROR",
                        "message": str(e)
                    }
                else:
                    raise
                    
            except frappe.PermissionError as e:
                # Handle permission errors
                if log_traceback:
                    frappe.log_error(
                        f"TrackFlow Permission Error: {str(e)}",
                        f"TrackFlow {error_type} Permission Error"
                    )
                
                if return_response:
                    return {
                        "status": "error",
                        "error_code": "PERMISSION_DENIED",
                        "message": _("You don't have permission to perform this action")
                    }
                else:
                    raise
                    
            except Exception as e:
                # Handle unexpected errors
                error_id = frappe.generate_hash(length=8)
                
                frappe.log_error(
                    f"TrackFlow {error_type} Error ID: {error_id}\n{traceback.format_exc()}",
                    f"TrackFlow {error_type} Error"
                )
                
                if frappe.conf.developer_mode:
                    error_message = str(e)
                else:
                    error_message = _("An unexpected error occurred. Error ID: {0}").format(error_id)
                
                if return_response:
                    return {
                        "status": "error",
                        "error_code": "INTERNAL_ERROR",
                        "message": error_message,
                        "error_id": error_id
                    }
                else:
                    raise
                    
        return wrapper
    return decorator

def validate_required_fields(data, required_fields):
    """Validate that all required fields are present in data
    
    Args:
        data: Dictionary to validate
        required_fields: List of required field names
        
    Raises:
        ValidationError: If any required field is missing
    """
    missing_fields = []
    
    for field in required_fields:
        if field not in data or not data.get(field):
            missing_fields.append(field)
    
    if missing_fields:
        raise ValidationError(
            _("Missing required fields: {0}").format(", ".join(missing_fields)),
            error_code="MISSING_FIELDS",
            details={"missing_fields": missing_fields}
        )

def validate_url(url):
    """Validate and sanitize URL
    
    Args:
        url: URL to validate
        
    Returns:
        Sanitized URL
        
    Raises:
        ValidationError: If URL is invalid
    """
    if not url:
        raise ValidationError(_("URL cannot be empty"))
    
    # Basic URL validation
    from urllib.parse import urlparse
    
    try:
        parsed = urlparse(url)
        
        if not parsed.scheme:
            # Add http:// if no scheme provided
            url = f"http://{url}"
            parsed = urlparse(url)
        
        if not parsed.netloc:
            raise ValidationError(_("Invalid URL format"))
        
        # Prevent XSS
        if any(char in url for char in ['<', '>', '"', "'"]):
            raise ValidationError(_("URL contains invalid characters"))
        
        return url
        
    except Exception as e:
        raise ValidationError(_("Invalid URL: {0}").format(str(e)))

def rate_limit_check(key, limit=100, window=3600):
    """Check rate limit for a given key
    
    Args:
        key: Unique key for rate limiting (e.g., IP address, user)
        limit: Maximum number of requests allowed
        window: Time window in seconds
        
    Returns:
        Tuple of (allowed, remaining_requests)
    """
    cache_key = f"trackflow_rate_limit:{key}"
    current_count = frappe.cache().get(cache_key) or 0
    
    if current_count >= limit:
        return False, 0
    
    # Increment counter
    new_count = current_count + 1
    frappe.cache().setex(cache_key, window, new_count)
    
    return True, limit - new_count

def sanitize_input(data, allowed_fields=None, max_length=None):
    """Sanitize input data
    
    Args:
        data: Dictionary to sanitize
        allowed_fields: List of allowed field names (if None, all fields are allowed)
        max_length: Maximum length for string values
        
    Returns:
        Sanitized data dictionary
    """
    if not isinstance(data, dict):
        return {}
    
    sanitized = {}
    
    for key, value in data.items():
        # Check if field is allowed
        if allowed_fields and key not in allowed_fields:
            continue
        
        # Sanitize based on type
        if isinstance(value, str):
            # Remove any HTML/script tags
            value = frappe.utils.strip_html_tags(value)
            
            # Limit length if specified
            if max_length and len(value) > max_length:
                value = value[:max_length]
                
        elif isinstance(value, (list, dict)):
            # Recursively sanitize nested structures
            value = sanitize_input(value, max_length=max_length)
        
        sanitized[key] = value
    
    return sanitized

def get_client_ip():
    """Get client IP address, considering proxies
    
    Returns:
        Client IP address
    """
    if not frappe.request:
        return None
    
    # Check for proxy headers
    for header in ['HTTP_X_FORWARDED_FOR', 'HTTP_X_REAL_IP', 'HTTP_CLIENT_IP']:
        ip = frappe.request.environ.get(header)
        if ip:
            # Take the first IP if there are multiple
            return ip.split(',')[0].strip()
    
    # Fall back to remote address
    return frappe.request.environ.get('REMOTE_ADDR')

def is_internal_ip(ip_address):
    """Check if IP address is internal
    
    Args:
        ip_address: IP address to check
        
    Returns:
        True if internal, False otherwise
    """
    if not ip_address:
        return False
    
    # Check against configured internal IP ranges
    internal_ranges = frappe.get_all(
        "Internal IP Range",
        fields=["ip_range"]
    )
    
    for ip_range_doc in internal_ranges:
        try:
            # Use ipaddress library to check CIDR ranges
            import ipaddress
            network = ipaddress.ip_network(ip_range_doc.ip_range, strict=False)
            if ipaddress.ip_address(ip_address) in network:
                return True
        except ValueError:
            # Skip invalid IP ranges
            continue
    
    # Check common private IP ranges
    private_ranges = [
        ("10.0.0.0", "10.255.255.255"),
        ("172.16.0.0", "172.31.255.255"),
        ("192.168.0.0", "192.168.255.255"),
        ("127.0.0.0", "127.255.255.255")
    ]
    
    for start, end in private_ranges:
        if is_ip_in_range(ip_address, start, end):
            return True
    
    return False

def is_ip_in_range(ip, start, end):
    """Check if IP is in range
    
    Args:
        ip: IP address to check
        start: Start of IP range
        end: End of IP range
        
    Returns:
        True if IP is in range, False otherwise
    """
    try:
        import ipaddress
        
        ip_obj = ipaddress.ip_address(ip)
        start_obj = ipaddress.ip_address(start)
        end_obj = ipaddress.ip_address(end)
        
        return start_obj <= ip_obj <= end_obj
        
    except Exception:
        return False

def log_activity(activity_type, details=None, severity="info"):
    """Log TrackFlow activity for audit purposes
    
    Args:
        activity_type: Type of activity
        details: Dictionary with activity details
        severity: Log severity (info, warning, error)
    """
    try:
        activity_log = frappe.new_doc("TrackFlow Activity Log")
        activity_log.activity_type = activity_type
        activity_log.severity = severity
        activity_log.user = frappe.session.user
        activity_log.ip_address = get_client_ip()
        activity_log.timestamp = frappe.utils.now()
        
        if details:
            activity_log.details = frappe.as_json(details)
        
        activity_log.insert(ignore_permissions=True)
        
    except Exception:
        # Don't let logging errors break the application
        pass
