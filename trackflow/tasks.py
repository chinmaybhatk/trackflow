"""
Scheduled tasks for TrackFlow
"""

import frappe


def process_visitor_sessions():
    """No-op: session tracking is on the roadmap (see SCHEMA_AUDIT P0 #3)."""
    return


def update_campaign_metrics():
    """Recalculate metrics for active campaigns"""
    try:
        campaigns = frappe.get_all("Link Campaign", filters={"status": "Active"}, pluck="name")

        for campaign_name in campaigns:
            total_clicks = frappe.db.sql(
                """SELECT IFNULL(SUM(click_count), 0) FROM `tabTracked Link`
                WHERE campaign = %s""",
                campaign_name,
            )[0][0]

            unique_visitors = frappe.db.sql(
                """SELECT IFNULL(SUM(unique_visitor_count), 0) FROM `tabTracked Link`
                WHERE campaign = %s""",
                campaign_name,
            )[0][0]

            conversions = frappe.db.count(
                "Click Event",
                filters={"campaign": campaign_name, "event_type": "conversion"},
            )

            conversion_rate = (conversions / total_clicks * 100) if total_clicks else 0

            frappe.db.set_value(
                "Link Campaign",
                campaign_name,
                {
                    "total_clicks": total_clicks,
                    "unique_visitors": unique_visitors,
                    "conversions": conversions,
                    "conversion_rate": conversion_rate,
                },
                update_modified=False,
            )

        if campaigns:
            frappe.db.commit()
    except Exception as e:
        frappe.log_error(f"update_campaign_metrics error: {e}", "TrackFlow Tasks")


def cleanup_expired_data():
    """Clean up old tracking data based on retention settings"""
    try:
        retention_days = 90
        if frappe.db.exists("TrackFlow Settings", "TrackFlow Settings"):
            settings = frappe.get_single("TrackFlow Settings")
            retention_days = getattr(settings, "data_retention_days", 90) or 90

        cutoff_date = frappe.utils.add_to_date(frappe.utils.today(), days=-retention_days)

        frappe.db.delete("Visitor Event", {"creation": ["<", cutoff_date]})
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(f"cleanup_expired_data error: {e}", "TrackFlow Tasks")


def calculate_attribution():
    """Calculate attribution for deals missing attribution data"""
    try:
        deals = frappe.get_all(
            "CRM Deal",
            filters={
                "trackflow_marketing_influenced": 1,
                "trackflow_attribution_model": ["is", "not set"],
            },
            pluck="name",
            limit=50,
        )

        for deal_name in deals:
            try:
                from trackflow.integrations.crm_deal import calculate_attribution as calc_attr

                deal_doc = frappe.get_doc("CRM Deal", deal_name)
                calc_attr(deal_doc, None)
            except Exception as e:
                frappe.log_error(f"Attribution error for {deal_name}: {e}", "TrackFlow Tasks")
    except Exception as e:
        frappe.log_error(f"calculate_attribution error: {e}", "TrackFlow Tasks")


def cleanup_old_visitors():
    """Remove anonymous visitors with no activity in 180 days"""
    try:
        cutoff_date = frappe.utils.add_to_date(frappe.utils.today(), days=-180)

        old_visitors = frappe.get_all(
            "Visitor",
            filters={"last_seen": ["<", cutoff_date]},
            pluck="name",
            limit=500,
        )

        for visitor_name in old_visitors:
            try:
                frappe.delete_doc("Visitor", visitor_name, ignore_permissions=True)
            except Exception:
                pass

        if old_visitors:
            frappe.db.commit()
    except Exception as e:
        frappe.log_error(f"cleanup_old_visitors error: {e}", "TrackFlow Tasks")
