import frappe
from frappe import _

def track_form_submission(doc, method=None):
    """
    Override for frappe.www.contact.send_message to track form submissions
    """
    # Call the original method first
    from frappe.www.contact import send_message as original_send_message
    result = original_send_message()
    
    # Track the submission
    try:
        # Get visitor ID from cookies
        visitor_id = frappe.local.request.cookies.get("trackflow_visitor_id")
        if visitor_id:
            from trackflow.tracking import track_event
            
            # Track contact form submission
            track_event(
                visitor_id=visitor_id,
                event_type="contact_form_submission",
                event_data={
                    "form_type": "contact",
                    "email": frappe.form_dict.get("email"),
                    "subject": frappe.form_dict.get("subject"),
                    "timestamp": frappe.utils.now()
                }
            )
            
            # Update visitor profile with contact info
            if frappe.form_dict.get("email"):
                from trackflow.utils import update_visitor_profile
                update_visitor_profile(visitor_id, {
                    "email": frappe.form_dict.get("email"),
                    "name": frappe.form_dict.get("name"),
                    "phone": frappe.form_dict.get("phone"),
                    "last_contact_date": frappe.utils.now()
                })
                
    except Exception as e:
        # Log error but don't break the original functionality
        frappe.log_error(f"TrackFlow contact form tracking error: {str(e)}")
    
    return result
