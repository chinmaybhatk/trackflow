# TrackFlow Schema Audit

A pass over the 29 doctypes in `trackflow/trackflow/doctype/` to identify schema/code mismatches, dead doctypes, and proposed cleanups.

> **Scope:** schema design and consistency only. Implementation bugs (e.g. visitor not being upserted) are tracked elsewhere.

---

## 🔥 P0 — Will cause runtime errors

> **Status:** P0 #1 shipped. P0 #2 (Internal IP Range refs) and #3 (Visitor Session) still open.

### 1. ~~`Conversion` vs `Link Conversion` split-brain~~ ✅ DONE (twice)

First pass (P0 #1): consolidated to `Link Conversion`. Second pass (post-audit user request): renamed `Link Conversion` → `Conversion` now that the conflict is gone.

Industry check: YOURLS uses no conversion concept (pure click counter). Bitly, Google Analytics, HubSpot all use "Conversion". TrackFlow now matches.

The doctype JSON also carries a description used in the UI:
> A Conversion is a downstream outcome (lead, signup, purchase, form submission, etc.) attributed to a tracked-link click. Click Event captures the visit; Conversion captures what happened next.
Two doctypes for the same concept; code is inconsistent.

| File | Uses |
|---|---|
| `trackflow/tracking.py:98` | `frappe.new_doc("Conversion")` |
| `trackflow/integrations/crm_lead.py:166` | `frappe.new_doc("Conversion")` |
| `trackflow/install.py:324` | references `Conversion` |
| `trackflow/trackflow/page/trackflow_dashboard/...py:43` | `frappe.db.count("Conversion", ...)` |
| `trackflow/integrations/crm_deal.py:141` | `frappe.new_doc("Link Conversion")` |
| `trackflow/integrations/crm_organization.py:82` | `frappe.new_doc("Link Conversion")` |
| `trackflow/integrations/web_form.py:76` | `frappe.new_doc("Link Conversion")` |
| `trackflow/api/campaign.py:50`, `analytics.py` | `frappe.db.count("Link Conversion", ...)` |

**Fields differ too:** `Conversion` has `conversion_date`, `conversion_value`, `document_name`. `Link Conversion` has `conversion_timestamp`, `tracked_link`, `campaign`, no `document_name`.

**Proposal:** Pick one. Recommend keeping `Link Conversion` (it's the newer, better-modeled one used by analytics). Delete `Conversion`. Migrate the 4-5 call sites. Add `document_name` to `Link Conversion` if cross-doctype attribution is wanted.

**Resolved:** All write-sites migrated to `Link Conversion`. Field map: `visitor` → `visitor_id`, `conversion_date` → `conversion_timestamp`, `linked_document_type` → `source_doctype`, `linked_document` → `source_document`, `metadata` → `conversion_metadata`. Auto-populated `click_event` + `tracked_link` from the visitor's most recent click. Mapped `conversion_type` to the Select options (`"Lead"` instead of `"lead_created"`). Fixed Link Conversion `lead` field options from `Lead` → `CRM Lead`. Verified end-to-end: lead creation triggers a conversion linked to visitor + click + lead. Doctype count: 19 → **18**.

### 2. ~~`Internal IP Range` doctype + 10 stale refs~~ ✅ DONE
We removed it from `error_handler.py` earlier. Other files still reference it.

**Files still referencing:**
- `trackflow/trackflow/doctype/trackflow_settings/...` (1)
- `trackflow/api/v1.py`, `trackflow/utils/__init__.py`, etc. (9)

**Proposal:** Either restore the doctype or remove all references. Recommend removing — modern internal-IP filtering can be a Settings text field with comma-separated CIDRs.

**Resolved:** Replaced `Internal IP Range` child table with a `internal_ip_ranges` `Small Text` field on `TrackFlow Settings` (one CIDR/prefix per line). Updated `utils.py` to parse line-separated tokens and `install.py` to seed defaults. Deleted the doctype, the legacy patches (`ensure_internal_ip_range_doctype`, `manual_fix_internal_ip_range`, `fix_ip_range_validation`), and the patches.txt entries.

### 3. ~~`Visitor Session` queried but never created~~ ✅ DONE
29 references in code, but no flow ever inserts a `Visitor Session` row. `get_lead_tracking_data` returns it as `session_history`, always empty.

**Proposal:** Either implement session tracking (a session = clicks within N min from same visitor), or remove the queries and the doctype. Quickest path: remove the queries; document Sessions as Roadmap.

**Resolved:** Followed the audit's quickest path. Deleted the `Visitor Session` doctype + folder. Stubbed `process_visitor_sessions` (scheduled task), `update_visitor_session` (api/tracking.py), `create_visitor_session` (utils.py + utils/__init__.py), `get_bounce_rate` (utils.py) and the `test_06_visitor_session_tracking` test. Removed Visitor Session refs from `dashboard.py`, `install.py`, `config/trackflow.py`, `tracking.py`. Swapped `tabVisitor Session` → `tabClick Event` in the conversion-funnel report. Deleted the dead `trackflow/trackflow/integrations/` folder (broken duplicate web_form.py + opportunity.py) and the unused `trackflow/trackflow/demo_data.py`. Per-session bucketing is now on the Roadmap.

Doctype count: 18 → **16**.

---

## ⚠️ P1 — Naming / consistency problems

> **Status:** P1 #4 and #5 shipped. P1 #6 deferred (see note below).

### 4. ~~`Campaign` vs `Link Campaign` overlap~~ ✅ DONE
Two campaign doctypes:
- `Campaign` — used by `email.py`, `dashboard.py`, `jinja_filters.py`, `campaign_performance_report.py`, `trackflow_dashboard`. Looks like the **email-marketing** flavor.
- `Link Campaign` — used by ~50 references. The **link-tracking** flavor. Has fields like `budget`, `start_date`, `end_date`, `status`.

**Proposal:** Merge into `Link Campaign` and add a `campaign_type` enum (Email / Link / Mixed). Update email tracking to use `Link Campaign` with `campaign_type=Email`. Removes 1 doctype.

**Resolved:** `Campaign` doctype deleted (had 0 records). All 6 callers migrated to `Link Campaign`. `Link Campaign` already had a `campaign_type` Select with options Email/Social/SEM/Content/Affiliate/Display/Direct Mail/Event/Other.

### 5. ~~`Click Event.click_timestamp` vs `creation`~~ ✅ DONE
Some queries filter on `creation` (`tabClick Event` in `analytics.py`), others on `click_timestamp` (in `crm_lead.py`). They're usually equal, but not always (if a click is backfilled).

**Proposal:** Standardize on `click_timestamp` everywhere. `creation` is a system field, not a business field.

**Resolved:** All `analytics.py` queries now use `click_timestamp` for Click Event and `conversion_timestamp` for Link Conversion. Verified `get_analytics(period="30days")` returns real numbers (5 clicks, 5 unique visitors).

### 6. Click Event UTM duplication ⏸ DEFERRED
`Click Event` has `utm_source`, `utm_medium`, `utm_campaign`, `utm_term`, `utm_content` AND `campaign` AND `short_code`. The `tracked_link` link already implies `campaign` and UTMs. This is denormalized data that can drift.

**Proposal:** Keep `utm_*` (we want frozen point-in-time values), drop the redundant `campaign` field (derivable from `tracked_link.campaign`).

**Deferred** because:
- 5+ files would need rewrites with JOINs through `tracked_link`, adding query overhead
- The field is set once at insert from `tracked_link.campaign`; tracked links rarely re-campaign, so drift risk is low
- Revisit if there's a concrete drift bug, or if the schema gets a major refactor

---

## 🪦 P2 — Orphaned doctypes ✅ DONE (all 9 deleted)

| Doctype | Status |
|---|---|
| `API Key IP Whitelist` | Deleted |
| `API Key Permission` | Deleted |
| `API Key Webhook Event` | Deleted |
| `API Request Log` | Deleted |
| `Attribution Channel Rule` | Deleted |
| `Campaign Link Variant` | Deleted |
| `Click Queue` | Deleted |
| `Domain Header Configuration` | Deleted |
| `Template Variable` | Deleted |

**Result:** 29 → 19 doctypes (−34%). All deletions clean — no foreign key cascades, no broken references.

### Doctypes with very few references (review needed)

| Doctype | Refs | Note |
|---|---|---|
| `Lead Status Change` | 1 | Single ref — likely scaffolding |
| `Deal Stage Change` | 2 | Same |
| `Deal Link Association` | 7 | Used but unverified end-to-end |
| `Visitor Event` | 5 | Overlaps with Click Event |
| `Link Template` | 1 | Likely scaffolding |
| `Domain Configuration` | 9 | Multi-domain support — useful if planned |

**Proposal:** Mark all but `Domain Configuration` as removal candidates pending verification.

---

## 📝 P3 — Smaller schema improvements

### 7. Visitor doctype gaps
Already partly fixed in this session (added `crm_lead`, `lead_created_date`). Still missing:
- `last_campaign` (Link Campaign) — for "what brought them back"
- `total_conversions` — currently computed from joins, could be a stored counter

### 8. Tracked Link missing some indexes
`short_code` is the primary lookup field on every redirect. Should be indexed (check JSON for `"unique": 1` or `search_index: 1`).

### 9. Settings: `internal_ip_ranges` text field
Replace the deleted `Internal IP Range` child table with a simple textarea on `TrackFlow Settings` accepting one CIDR per line. Simpler, faster to query.

### 10. Naming consistency
Folder names use `lower_snake_case` (correct). DocType labels use `Title Case`. The mismatch is fine, but two stand out:
- `TrackFlow Settings` (correct) vs folder `trackflow_settings`
- `TrackFlow API Key` — folder is `trackflow_api_key`

These follow Frappe conventions, **no change needed**.

---

## ✅ Doctypes in good shape

| Doctype | Notes |
|---|---|
| `Tracked Link` | Healthy. Added QR fields recently |
| `Click Event` | Clean schema, see UTM denorm note |
| `Visitor` | Just cleaned up in this session |
| `Link Campaign` | Solid base; absorb `Campaign` into it (P1) |
| `Link Conversion` | Solid; absorb `Conversion` into it (P0) |
| `TrackFlow Settings` | Singleton, working |

---

## 📋 Recommended sequence

1. **P0-1**: Consolidate `Conversion` → `Link Conversion` (one focused PR)
2. **P0-2**: Remove `Internal IP Range` references, replace with Settings textarea
3. **P0-3**: Remove `Visitor Session` queries from `get_lead_tracking_data` (or implement sessions properly — Roadmap)
4. **P2**: Delete the 9 orphaned doctypes (one cleanup PR)
5. **P1-4**: Merge `Campaign` into `Link Campaign` with a `campaign_type` field
6. **P1-5**: Standardize Click Event timestamps on `click_timestamp`
7. **P3**: Visitor + Settings small additions

Steps 1–4 are low-risk and would reduce the doctype count from 29 to ~18.

---

*Generated as part of session schema review. Not a commitment to ship — these are proposals to discuss before implementation.*
