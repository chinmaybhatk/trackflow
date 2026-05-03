"""
TrackFlow REST API v1
"""

import frappe
from frappe import _
from frappe.utils import now_datetime
import json
from urllib.parse import urlencode, urlparse, parse_qs, urlunparse


@frappe.whitelist(allow_guest=True)
def track_click(short_code=None):
    """Track a click on a short link and redirect"""
    if not short_code:
        frappe.throw(_("Invalid link"))

    link = frappe.db.get_value(
        "Tracked Link",
        {"short_code": short_code, "status": "Active"},
        ["name", "target_url", "destination_url", "campaign", "source", "medium"],
        as_dict=True,
    )

    if not link:
        frappe.throw(_("Link not found or inactive"), frappe.DoesNotExistError)

    from trackflow.trackflow.utils import generate_visitor_id, create_click_event

    visitor_id = (
        frappe.request.cookies.get("trackflow_visitor") if frappe.request else None
    )
    if not visitor_id:
        visitor_id = generate_visitor_id()

    link_doc = frappe.get_doc("Tracked Link", link.name)

    request_data = {}
    if frappe.request:
        request_data = {
            "ip": frappe.request.headers.get("X-Forwarded-For", frappe.request.remote_addr),
            "user_agent": frappe.request.headers.get("User-Agent", ""),
            "referrer": frappe.request.headers.get("Referer", ""),
        }

    create_click_event(link_doc, visitor_id, request_data)

    frappe.db.sql(
        """UPDATE `tabTracked Link`
        SET click_count = IFNULL(click_count, 0) + 1, last_click = %s
        WHERE name = %s""",
        (frappe.utils.now(), link.name),
    )
    frappe.db.commit()

    final_url = _build_final_url(link)

    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = final_url


@frappe.whitelist()
def create_link(url, campaign=None, title=None, source=None, medium=None, **kwargs):
    """Create a new tracked link"""
    if not url or not url.startswith(("http://", "https://")):
        frappe.throw(_("Please provide a valid URL"))

    link = frappe.new_doc("Tracked Link")
    link.title = title or url[:140]
    link.target_url = url
    link.destination_url = url
    link.campaign = campaign
    link.source = source
    link.medium = medium
    link.status = "Active"

    if kwargs.get("expiry_date"):
        link.expiry_date = kwargs["expiry_date"]

    link.insert()

    site_url = frappe.utils.get_url()
    return {
        "success": True,
        "name": link.name,
        "short_code": link.short_code,
        "tracking_url": f"{site_url}/r/{link.short_code}",
    }


@frappe.whitelist()
def get_analytics(short_code=None, campaign=None, period="7d"):
    """Get analytics for a link or campaign"""
    filters = {}

    if short_code:
        link_name = frappe.db.get_value("Tracked Link", {"short_code": short_code}, "name")
        if not link_name:
            frappe.throw(_("Link not found"))
        filters["tracked_link"] = link_name
    elif campaign:
        filters["campaign"] = campaign
    else:
        frappe.throw(_("Please provide either short_code or campaign"))

    date_range = _get_date_range(period)
    filters["click_timestamp"] = ["between", date_range]

    clicks = frappe.get_all(
        "Click Event",
        filters=filters,
        fields=["click_timestamp", "ip_address", "user_agent", "referrer", "utm_source", "utm_medium"],
        order_by="click_timestamp desc",
        limit=500,
    )

    return {
        "success": True,
        "period": period,
        "total_clicks": len(clicks),
        "clicks": clicks[:100],
    }


@frappe.whitelist()
def bulk_create_links(links):
    """Create multiple tracked links at once"""
    if isinstance(links, str):
        links = json.loads(links)

    created = []
    errors = []

    for link_data in links:
        try:
            result = create_link(**link_data)
            created.append(result)
        except Exception as e:
            errors.append({"url": link_data.get("url"), "error": str(e)})

    return {"success": len(errors) == 0, "created": len(created), "links": created, "errors": errors}


def _build_final_url(link):
    """Build final URL with UTM parameters"""
    url = link.target_url or link.destination_url
    if not url:
        return "/"

    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    if link.source and "utm_source" not in params:
        params["utm_source"] = [link.source]
    if link.medium and "utm_medium" not in params:
        params["utm_medium"] = [link.medium]
    if link.campaign:
        campaign_name = frappe.db.get_value("Link Campaign", link.campaign, "campaign_name")
        if campaign_name and "utm_campaign" not in params:
            params["utm_campaign"] = [campaign_name]

    updated_query = urlencode(params, doseq=True)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, updated_query, parsed.fragment))


def _get_date_range(period):
    """Convert period string to date range"""
    from frappe.utils import add_days, get_datetime

    end_date = get_datetime()
    days_map = {"1d": -1, "7d": -7, "30d": -30, "90d": -90}
    start_date = add_days(end_date, days_map.get(period, -7))
    return [start_date, end_date]
