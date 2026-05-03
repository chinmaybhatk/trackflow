import frappe
from frappe import _
from trackflow.trackflow.utils import create_click_event, generate_visitor_id

no_cache = 1


def get_context(context):
    """Handle redirect for tracked links"""
    path_parts = frappe.request.path.strip("/").split("/")

    if len(path_parts) < 2:
        frappe.throw(_("Invalid tracking link"), frappe.DoesNotExistError)

    tracking_id = path_parts[-1]

    tracked_link = frappe.db.get_value(
        "Tracked Link",
        {"short_code": tracking_id, "status": "Active"},
        ["name", "target_url", "campaign", "source", "medium"],
        as_dict=True,
    )

    if not tracked_link:
        frappe.throw(_("Link not found or expired"), frappe.DoesNotExistError)

    tracked_link_doc = frappe.get_doc("Tracked Link", tracked_link.name)

    if (
        tracked_link_doc.expiry_date
        and frappe.utils.get_datetime(tracked_link_doc.expiry_date)
        < frappe.utils.now_datetime()
    ):
        tracked_link_doc.status = "Expired"
        tracked_link_doc.save(ignore_permissions=True)
        frappe.throw(_("Link has expired"), frappe.DoesNotExistError)

    try:
        visitor_id = frappe.request.cookies.get("trackflow_visitor")

        if not visitor_id:
            visitor_id = generate_visitor_id()
            frappe.local.cookie_manager.set_cookie(
                "trackflow_visitor",
                visitor_id,
                expires=365 * 24 * 60 * 60,
            )

        request_data = {
            "ip": frappe.local.request_ip or frappe.request.environ.get("REMOTE_ADDR"),
            "user_agent": frappe.request.headers.get("User-Agent", ""),
            "referrer": frappe.request.headers.get("Referer", ""),
        }

        click_event = create_click_event(tracked_link_doc, visitor_id, request_data)

        frappe.db.sql(
            """
            UPDATE `tabTracked Link`
            SET
                click_count = IFNULL(click_count, 0) + 1,
                last_click = %s
            WHERE name = %s
        """,
            (frappe.utils.now(), tracked_link_doc.name),
        )

        if click_event and not frappe.db.exists(
            "Click Event",
            {
                "tracked_link": tracked_link_doc.name,
                "visitor_id": visitor_id,
                "name": ["!=", click_event.name],
            },
        ):
            frappe.db.sql(
                """
                UPDATE `tabTracked Link`
                SET unique_visitor_count = IFNULL(unique_visitor_count, 0) + 1
                WHERE name = %s
            """,
                tracked_link_doc.name,
            )

        frappe.db.commit()

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Click Event Tracking Error")

    destination_url = tracked_link.target_url

    if not destination_url:
        frappe.throw(_("Invalid destination URL"), frappe.ValidationError)

    from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

    parsed_url = urlparse(destination_url)
    params = parse_qs(parsed_url.query)

    if tracked_link.campaign and "utm_campaign" not in params:
        campaign = frappe.get_doc("Link Campaign", tracked_link.campaign)
        params["utm_campaign"] = [campaign.campaign_name]

    if tracked_link.source and "utm_source" not in params:
        params["utm_source"] = [tracked_link.source]

    if tracked_link.medium and "utm_medium" not in params:
        params["utm_medium"] = [tracked_link.medium]

    if visitor_id:
        params["tf_visitor"] = [visitor_id]

    updated_query = urlencode(params, doseq=True)
    final_url = urlunparse(
        (
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            parsed_url.params,
            updated_query,
            parsed_url.fragment,
        )
    )

    frappe.flags.redirect_location = final_url
    raise frappe.Redirect
