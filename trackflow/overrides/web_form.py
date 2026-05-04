"""Override for Frappe's Web Form `accept` endpoint.

Wraps the upstream submission flow so that any web form which has
`trackflow_tracking_enabled` set produces a Conversion record attributed
to the visitor's most recent tracked-link click.

A Conversion is a downstream outcome (lead, signup, purchase, form
submission, etc.) attributed to a tracked-link click. Click Event
captures the visit; Conversion captures what happened next.
"""

import frappe
from frappe import _


@frappe.whitelist(allow_guest=True)
def accept(web_form, data):
    """Drop-in replacement for `frappe.website.doctype.web_form.web_form.accept`.

    Calls the original implementation, then — if the Web Form has
    TrackFlow tracking enabled — records a Conversion linked back to
    the visitor's most recent click.
    """
    from frappe.website.doctype.web_form.web_form import accept as upstream_accept

    # Run the real submission first so any error (validation, mandatory
    # fields, etc.) bubbles up unchanged.
    result = upstream_accept(web_form, data)

    try:
        _record_web_form_conversion(web_form)
    except Exception:
        # Never let TrackFlow break a real form submission.
        frappe.log_error(frappe.get_traceback(), "TrackFlow Web Form Conversion")

    return result


def _record_web_form_conversion(web_form_name):
    """Create a Conversion row for the just-submitted form, if eligible."""
    wf = frappe.db.get_value(
        "Web Form",
        web_form_name,
        ["doc_type", "trackflow_tracking_enabled", "trackflow_conversion_goal"],
        as_dict=True,
    )
    if not wf or not wf.get("trackflow_tracking_enabled"):
        return

    visitor_id = _resolve_visitor_id()
    if not visitor_id:
        return

    last_click = frappe.db.sql(
        """
        SELECT name, tracked_link
        FROM `tabClick Event`
        WHERE visitor_id = %s
        ORDER BY click_timestamp DESC
        LIMIT 1
        """,
        visitor_id,
        as_dict=True,
    )
    if not last_click:
        # Conversion requires a click_event + tracked_link (mandatory fields).
        return

    target_doctype = wf.doc_type
    target_doc_name = _resolve_target_doc_name(target_doctype, visitor_id)

    conversion = frappe.new_doc("Conversion")
    conversion.visitor_id = visitor_id
    conversion.click_event = last_click[0].name
    conversion.tracked_link = last_click[0].tracked_link
    conversion.conversion_type = _map_conversion_type(target_doctype)
    conversion.conversion_timestamp = frappe.utils.now()
    if wf.get("trackflow_conversion_goal"):
        conversion.campaign = wf["trackflow_conversion_goal"]
    if target_doctype:
        conversion.source_doctype = target_doctype
    if target_doc_name:
        conversion.source_document = target_doc_name
        if target_doctype == "CRM Lead":
            conversion.lead = target_doc_name
        elif target_doctype == "CRM Deal":
            conversion.deal = target_doc_name
        elif target_doctype == "Contact":
            conversion.contact = target_doc_name
    conversion.conversion_metadata = frappe.as_json({
        "web_form": web_form_name,
        "doctype": target_doctype,
        "document": target_doc_name,
    })
    conversion.insert(ignore_permissions=True)


def _resolve_visitor_id():
    """Same lookup order as the CRM Lead before_insert hook."""
    try:
        form_dict = getattr(frappe, "form_dict", None)
        if form_dict:
            v = form_dict.get("tf_visitor") or form_dict.get("trackflow_visitor")
            if v:
                return v
        request = getattr(frappe, "request", None)
        if request and getattr(request, "cookies", None):
            return request.cookies.get("trackflow_visitor")
    except Exception:
        pass
    return None


def _resolve_target_doc_name(doctype, visitor_id):
    """Best-effort lookup of the document the web form just created/updated.

    Frappe's accept() doesn't return the doc, so we infer it from the
    most recent record of this doctype that mentions the visitor (if the
    target has a trackflow_visitor_id field) or from form_dict.name.
    """
    if not doctype:
        return None
    name = (frappe.form_dict or {}).get("name")
    if name and frappe.db.exists(doctype, name):
        return name
    # Try the trackflow_visitor_id custom field (CRM Lead has it).
    meta = frappe.get_meta(doctype)
    if meta.has_field("trackflow_visitor_id"):
        latest = frappe.db.sql(
            f"SELECT name FROM `tab{doctype}` "
            f"WHERE trackflow_visitor_id = %s ORDER BY creation DESC LIMIT 1",
            visitor_id,
        )
        if latest:
            return latest[0][0]
    return None


def _map_conversion_type(doctype):
    """Map the web form's target doctype to one of the Conversion.conversion_type Select options."""
    if doctype in ("CRM Lead", "Lead"):
        return "Lead"
    if doctype in ("CRM Deal", "Opportunity"):
        return "Purchase"
    if doctype == "Contact":
        return "Sign Up"
    return "Contact Form"
