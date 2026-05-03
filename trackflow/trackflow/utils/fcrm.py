"""
FCRM (Frappe CRM) compatibility helpers for TrackFlow.

TrackFlow works in two modes:
  - Standalone  : only TrackFlow is installed. Link tracking, QR codes, and
                  click analytics work fully. CRM-specific features are skipped.
  - With FCRM   : Frappe CRM is also installed. Attribution is wired to
                  CRM Lead, CRM Deal, and CRM Organization automatically.

Use `is_fcrm_installed()` anywhere you need to gate CRM-specific logic.
"""

import frappe


def is_fcrm_installed() -> bool:
    """Return True if Frappe CRM is present on this site."""
    return "crm" in frappe.get_installed_apps()


def fcrm_doctype_exists(doctype: str) -> bool:
    """Return True if a CRM DocType exists (extra safety check)."""
    return bool(frappe.db.exists("DocType", doctype))


def require_fcrm(feature_name: str = "This feature") -> None:
    """
    Raise a user-friendly error when a CRM-dependent feature is called
    on a site without Frappe CRM.
    """
    if not is_fcrm_installed():
        frappe.throw(
            f"{feature_name} requires Frappe CRM to be installed. "
            "TrackFlow's link tracking and QR features work without it.",
            title="Frappe CRM Not Installed",
        )
