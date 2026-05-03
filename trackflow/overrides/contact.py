import frappe


def track_form_submission(*args, **kwargs):
    """Override for frappe.www.contact.send_message to track form submissions"""
    from frappe.www.contact import send_message as original_send_message

    result = original_send_message(*args, **kwargs)

    try:
        visitor_id = frappe.request.cookies.get("trackflow_visitor") if frappe.request else None
        if visitor_id:
            from trackflow.tracking import track_event

            track_event(
                visitor_id=visitor_id,
                event_type="contact_form_submission",
                event_data={
                    "form_type": "contact",
                    "email": frappe.form_dict.get("email"),
                    "subject": frappe.form_dict.get("subject"),
                },
            )
    except Exception as e:
        frappe.log_error(f"TrackFlow contact tracking error: {str(e)}", "TrackFlow")

    return result
