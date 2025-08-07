# TrackFlow - Internal Server Error Troubleshooting

## Current Status
The TrackFlow app has been successfully installed, but the main site is showing an Internal Server Error. Here's what has been done so far:

### ✅ Fixed Issues:
1. **Migration errors** - Fixed by updating tracking.py to handle missing Visitor DocTypes
2. **Web form integration** - Fixed by adding proper error handling in web_form.py
3. **Installation issues** - Fixed by preventing workspace validation errors in install.py
4. **Permissions module** - Updated to use correct DocType names (Tracked Link, Link Campaign)
5. **After request hook** - Improved error handling to prevent crashes

### 🔧 Temporary Changes:
1. **Disabled after_request hook** in hooks.py to isolate the issue

## Next Steps to Debug

### 1. Test the diagnostic endpoints
Visit these URLs to check the app status:
- https://meta-app.frappe.cloud/api/method/trackflow.api.debug.test
- https://meta-app.frappe.cloud/api/method/trackflow.api.debug.debug
- https://meta-app.frappe.cloud/api/method/trackflow.api.debug.diagnose_error

### 2. Check server logs
SSH into the server and check the error logs:
```bash
# Check Frappe error logs
bench --site meta-app.frappe.cloud console
frappe.get_all("Error Log", filters={"creation": (">", "2025-08-07")}, fields=["method", "error"], order_by="creation desc", limit=10)

# Check nginx logs
sudo tail -n 100 /var/log/nginx/error.log

# Check supervisor logs
sudo supervisorctl tail -f meta-app.frappe.cloud-web:*
```

### 3. Clear cache and restart
```bash
bench --site meta-app.frappe.cloud clear-cache
bench --site meta-app.frappe.cloud clear-website-cache
bench restart
```

### 4. Re-enable after_request hook
Once the site is loading, uncomment the after_request line in hooks.py:
```python
# Change this:
# after_request = ["trackflow.tracking.after_request"]

# To this:
after_request = ["trackflow.tracking.after_request"]
```

### 5. Create missing DocTypes (if needed)
The app references several DocTypes that don't exist yet:
- Visitor
- Visitor Event
- Visitor Session
- Conversion
- Campaign (should be Link Campaign)
- Tracking Link (should be Tracked Link)

### 6. Check for conflicts
Make sure there are no conflicts with other apps or customizations:
```bash
bench --site meta-app.frappe.cloud console
# Check installed apps
frappe.get_installed_apps()

# Check for any custom scripts or server scripts
frappe.get_all("Server Script", fields=["name", "script_type", "module"])
```

## Quick Fixes to Try

### Option 1: Safe Mode
Create a minimal hooks.py that only includes essential components:
```python
app_name = "trackflow"
app_title = "TrackFlow"
app_publisher = "Chinmay Bhat"
app_description = "Smart link tracking and attribution for Frappe CRM"
app_email = "support@trackflow.app"
app_license = "MIT"

# Minimal configuration to get the site working
modules = {
    "TrackFlow": {
        "color": "#2563eb",
        "icon": "fa fa-link",
        "type": "module",
        "label": "TrackFlow"
    }
}

# Only essential API endpoints
rest_api_methods = [
    "trackflow.api.debug.test",
    "trackflow.api.debug.debug",
    "trackflow.api.debug.diagnose_error"
]
```

### Option 2: Check for Circular Imports
The error might be caused by circular imports. Check if any of the integration modules are importing each other.

### Option 3: Database Schema Issues
Check if all tables were created properly:
```python
# In bench console
tables = frappe.db.get_tables()
trackflow_tables = [t for t in tables if 'trackflow' in t or 'tracked_link' in t or 'click_event' in t]
print(trackflow_tables)
```

## Contact
If you need further assistance, please provide:
1. The output from the diagnostic endpoints
2. Any error messages from the server logs
3. The result of the database schema check
