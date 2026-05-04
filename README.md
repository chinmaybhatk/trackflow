# TrackFlow — Link Tracking & Attribution for Frappe

[![Frappe](https://img.shields.io/badge/Frappe-v16-blue.svg)](https://frappeframework.com) [![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE) [![Python](https://img.shields.io/badge/python-3.14%2B-blue.svg)](https://python.org)

TrackFlow is a link-tracking app for Frappe v16. It generates short trackable URLs (with QR codes), captures click events with visitor identification, and exposes the data through Frappe's standard list views and form analytics. It can run standalone or alongside Frappe CRM.

> **Status:** This README only documents features that are verified working today. Planned and partially-implemented features live in the [Roadmap](#-roadmap) section. Things not yet working are listed under [Known Issues](#-known-issues).

---

## ✅ Features

### Tracked Links
- Create a Tracked Link with a destination URL
- Short code auto-generated (e.g. `4oATbZ`); short URL: `https://your-site/r/<code>`
- Copy short link from the form's top banner
- Soft fields: title, expiry date, status (Active/Inactive), UTM parameters (campaign, source, medium, content, term)
- Click count, unique visitor count, last click timestamp on the form

### QR Code Generation
- QR code PNG auto-generated on insert and stored as a public File attachment
- "Regenerate QR" button on form toolbar (forces refresh)
- "Download PNG" and "Copy QR URL" actions in the QR preview block

### Click Tracking & Redirect
- `/r/<short_code>` redirects (HTTP 301) to the destination URL
- Each click creates a `Click Event` record (visitor ID, timestamp, IP, user-agent)
- Visitor identification via `tf_visitor` query parameter appended to the destination URL
- Click count and unique visitor count update on the Tracked Link form

### Click Event Analytics
- The 📊 **Analytics** button on a Tracked Link opens the Click Event list filtered by that link
- Standard Frappe list filters / exports / reports work on Click Events

### Frappe v16 Desk Workspace
- TrackFlow registers as its own app in the Frappe desk (`/desk/trackflow`)
- Sidebar: **Home**, **Dashboard**, **Campaigns**, **Tracked Links**
- Shortcut cards on the workspace home: Dashboard, Campaigns, Tracked Links, Settings
- Workspace fixture (`trackflow/fixtures/trackflow_workspace.json`) is reapplied on `bench migrate`

### Standalone Mode
- TrackFlow installs cleanly without Frappe CRM present
- FCRM-specific custom fields (`trackflow_visitor_id`, etc.) are skipped when CRM is not installed
- Helper: `trackflow.trackflow.utils.fcrm.is_fcrm_installed()`

### Web Form → CRM Lead Attribution *(requires Frappe CRM)*
- When a tracked link redirects a user to a Frappe web form on the same site, the visitor is captured via the `tf_visitor` URL param and `trackflow_visitor` cookie
- On lead creation, a `before_insert` hook stamps `trackflow_visitor_id` plus the last-touch `source` / `medium` / `campaign` onto the `CRM Lead`
- A `Visitor` record is auto-created (on first click) and linked back to the lead (`Visitor.crm_lead`, `lead_created_date`)
- Engagement score on the Visitor reflects clicks, page views, conversions, and lead linkage

---

## 💻 Installation

### Prerequisites
- **Frappe Framework v16+** with Python 3.14+
- **Node.js 24+** for asset builds
- **MariaDB/MySQL** database backend
- **Administrator access** to your Frappe site
- *(Optional)* **Frappe CRM** for lead/deal integration features

### Install

```bash
cd ~/frappe-bench

bench get-app https://github.com/chinmaybhatk/trackflow.git
bench --site your-site-name install-app trackflow
bench --site your-site-name migrate
bench build --app trackflow
bench restart
```

### First-Run Setup

1. **Open the workspace**: navigate to `https://your-site/desk/trackflow`
2. **Configure settings** (Settings shortcut on workspace, or `/app/trackflow-settings`): enable tracking, set short-code length, choose attribution model
3. **Create a Tracked Link** (Tracked Links → +): set Title and Destination URL, save — short URL and QR code are generated immediately
4. **Test the redirect**: open the short URL — it should redirect (301) to the destination with `?tf_visitor=v_<id>` appended
5. **View clicks**: open the Tracked Link form → 📊 Analytics button → Click Events filtered by that link

> **Note**: Frappe CRM is a separate SPA at `/crm/` and does **not** host the TrackFlow workspace. Use `/desk/trackflow` for TrackFlow.

---

## 🗂️ Architecture

**Active DocTypes**

| DocType | Purpose |
|---|---|
| `Tracked Link` | Short URL + UTM + QR + click stats |
| `Link Campaign` | Group of tracked links with budget |
| `Click Event` | One row per click (visitor, timestamp, IP, UA) |
| `Visitor` | Persistent visitor identity |
| `Conversion` | A downstream outcome (lead, signup, purchase, form submission, etc.) attributed to a tracked-link click. Click Event = the visit; Conversion = what happened next. |
| `TrackFlow Settings` | Site-wide singleton config |

**Routes**

| Route | Purpose |
|---|---|
| `/r/<short_code>` | Click redirect (301) + tracking |
| `/t/<short_code>` | Alias for `/r/` |
| `/api/method/trackflow.api.tracking.*` | Tracking endpoints |
| `/api/method/trackflow.api.links.*` | Link management endpoints |

---

## 🚧 Roadmap

The following features are scaffolded in the codebase but are **not yet end-to-end verified**. Treat them as work-in-progress until they get their own row in [Features](#-what-works-today).

### Attribution & CRM Integration
- Multi-touch attribution models (Last Touch / First Touch / Linear / Time Decay / Position-Based)
- Auto-link `CRM Lead` → visitor via `trackflow_visitor_id` custom field
- `CRM Deal` revenue attribution and "marketing influenced" flag
- Per-deal attribution PDF report (`trackflow.api.reports.generate_attribution_pdf`)

### Campaign Analytics
- Campaign performance dashboard (clicks, unique visitors, conversions, ROI)
- Top-campaigns / source-breakdown / time-series APIs (`trackflow.api.analytics.*`)
- Visitor journey timeline view

### Email Tracking
- 1×1 pixel open tracking (`trackflow.api.email.track_email_open`)
- Wrapped link click tracking inside email HTML (`wrap_email_links`)
- Email Campaign Log aggregation

### Web Form: deeper integration
- Conversion goal tracking on Web Form save (the hook scaffolding exists but the conversion record is not yet created from web-form submissions)
- Auto-injection of a hidden `tf_visitor` field into Frappe web form HTML so cross-domain submissions work too

### Other planned items
- Cross-domain JS tracking embed for external sites (WordPress, Shopify, etc.)
- Bulk link generation API
- GDPR consent management UI
- Internal IP / employee traffic exclusion
- Webhooks on conversion / threshold alerts

---

## 🐛 Known Issues

- **No "Link Analytics" query report** — the original button referenced a report that was never created. The button now opens the Click Event list filtered by the link instead. A proper aggregated report is on the roadmap.
- **No CRM frontend integration** — TrackFlow only appears in the Frappe desk (`/desk/trackflow`), not inside the Frappe CRM SPA at `/crm/`. CRM integration is data-level only (via custom fields).
- **`bench clear-cache` interrupts active desk sessions** — after a cache clear you may need to hard-reload the browser (Cmd/Ctrl+Shift+R) to recover the workspace sidebar.
- **Workspace `content` field cannot contain HTML with quoted attributes** — the boot-info serializer mangles `\"` escapes. The TrackFlow workspace uses a plain-text header; do not add inline HTML with attributes.
- **Several admin/diagnostic API methods are unverified** — e.g. `trackflow.api.debug.*`, `trackflow.api.emergency.*`. Review before exposing.
- **Frontend SPA (`/frontend/`)** — a Vue dashboard exists in the repo but is not wired into the install flow.

---

## 🛠️ Development

```bash
# Bench dev server
bench start

# Rebuild after JS/JSON changes
bench build --app trackflow

# Apply doctype/fixture changes
bench --site your-site-name migrate

# Clear cache after fixture or boot-info changes
bench --site your-site-name clear-cache
```

See [GETTING_STARTED.md](GETTING_STARTED.md) for the full setup walkthrough and [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

---

## 📄 License

MIT — see [LICENSE](LICENSE).

## 👨‍💻 Author

**Chinmay Bhat** — [@chinmaybhatk](https://github.com/chinmaybhatk) · [chinmaybhatk@gmail.com](mailto:chinmaybhatk@gmail.com)

## 🆘 Support

- 🐛 **Bugs**: [GitHub Issues](https://github.com/chinmaybhatk/trackflow/issues)
- 💬 **Discussion**: [GitHub Discussions](https://github.com/chinmaybhatk/trackflow/discussions)
