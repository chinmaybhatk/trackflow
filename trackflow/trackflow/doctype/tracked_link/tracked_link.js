// Copyright (c) 2024, chinmaybhatk and contributors
// For license information, please see license.txt

frappe.ui.form.on('Tracked Link', {
    refresh: function (frm) {
        // Allow attaching links to campaigns that are still being prepared
        // (Planned) or currently running (Active). Hide finished campaigns.
        frm.set_query('campaign', function () {
            return { filters: { 'status': ['in', ['Planned', 'Active']] } };
        });

        if (!frm.is_new()) {
            frm.events.render_link_panel(frm);

            // Primary action: copy link
            frm.add_custom_button(__('📋 Copy Short Link'), function () {
                frm.events.copy_tracking_link(frm);
            }).addClass('btn-primary');

            // Regenerate QR (useful when short_code was manually set)
            frm.add_custom_button(__('↻ Regenerate QR'), function () {
                frappe.show_alert({ message: __('Generating QR code…'), indicator: 'blue' });
                frappe.call({
                    method: 'trackflow.trackflow.doctype.tracked_link.tracked_link.regenerate_qr',
                    args: { name: frm.doc.name },
                    callback: function (r) {
                        if (r.message) {
                            frm.reload_doc();
                            frappe.show_alert({ message: __('QR code updated!'), indicator: 'green' });
                        }
                    }
                });
            });

            frm.add_custom_button(__('📊 Analytics'), function () {
                frappe.set_route('List', 'Click Event', {
                    tracked_link: frm.doc.name
                });
            });
        }
    },

    // ---------------------------------------------------------------
    // Render the short-URL banner + QR preview at the top of the form
    // ---------------------------------------------------------------
    render_link_panel: function (frm) {
        const short_url = frm.events.get_tracking_url(frm);

        // Inject once per refresh – remove stale copy first
        frm.fields_dict.title.$wrapper.find('.tf-link-panel').remove();

        /* ── Short URL Banner ── */
        const banner = $(`
            <div class="tf-link-panel" style="
                background: #eff6ff;
                border: 1px solid #bfdbfe;
                border-radius: 8px;
                padding: 12px 16px;
                margin-bottom: 10px;
                display: flex;
                align-items: center;
                gap: 10px;
            ">
                <span style="font-size:20px; flex-shrink:0;">🔗</span>
                <div style="flex:1; min-width:0; overflow:hidden;">
                    <div style="font-size:10px; font-weight:700; color:#64748b;
                                text-transform:uppercase; letter-spacing:.6px; margin-bottom:2px;">
                        Short URL
                    </div>
                    <a href="${short_url}" target="_blank" style="
                        font-size:13px; font-weight:600; color:#1d4ed8;
                        text-decoration:none; word-break:break-all; display:block;
                    ">${short_url}</a>
                </div>
                <button class="btn btn-xs btn-default tf-copy-btn" style="flex-shrink:0; white-space:nowrap;">
                    Copy
                </button>
            </div>
        `);

        banner.find('.tf-copy-btn').on('click', function () {
            frm.events.copy_tracking_link(frm);
        });

        frm.fields_dict.title.$wrapper.prepend(banner);

        /* ── QR Preview (shown only when qr_code is populated) ── */
        if (frm.doc.qr_code) {
            frm.events.render_qr_preview(frm, short_url);
        }
    },

    render_qr_preview: function (frm, short_url) {
        frm.fields_dict.title.$wrapper.find('.tf-qr-panel').remove();

        const qr_src = frm.doc.qr_code;

        const panel = $(`
            <div class="tf-qr-panel" style="
                display: flex;
                align-items: flex-start;
                gap: 14px;
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 12px 16px;
                margin-bottom: 10px;
            ">
                <a href="${qr_src}" download="qr_${frm.doc.short_code}.png" title="Click to download">
                    <img src="${qr_src}" style="
                        width: 88px; height: 88px;
                        border-radius: 6px;
                        border: 1px solid #cbd5e1;
                        cursor: pointer;
                        display: block;
                    " />
                </a>
                <div>
                    <div style="font-size:10px; font-weight:700; color:#64748b;
                                text-transform:uppercase; letter-spacing:.6px; margin-bottom:4px;">
                        QR Code
                    </div>
                    <div style="font-size:11px; color:#475569; margin-bottom:8px; word-break:break-all;">
                        ${short_url}
                    </div>
                    <div style="display:flex; gap:6px; flex-wrap:wrap;">
                        <a href="${qr_src}" download="qr_${frm.doc.short_code}.png"
                           class="btn btn-xs btn-default" style="text-decoration:none;">
                            ⬇ Download PNG
                        </a>
                        <button class="btn btn-xs btn-default tf-copy-qr-url" data-url="${qr_src}">
                            📋 Copy QR URL
                        </button>
                    </div>
                </div>
            </div>
        `);

        panel.find('.tf-copy-qr-url').on('click', function () {
            const url = $(this).data('url');
            navigator.clipboard && navigator.clipboard.writeText(url).then(function () {
                frappe.show_alert({ message: __('QR URL copied!'), indicator: 'green' });
            });
        });

        frm.fields_dict.title.$wrapper.find('.tf-link-panel').after(panel);
    },

    // ---------------------------------------------------------------
    // Auto-fill source / medium from campaign
    // ---------------------------------------------------------------
    campaign: function (frm) {
        if (frm.doc.campaign) {
            frappe.db.get_value('Link Campaign', frm.doc.campaign, ['source', 'medium'], function (r) {
                if (r) {
                    if (r.source && !frm.doc.source) frm.set_value('source', r.source);
                    if (r.medium && !frm.doc.medium) frm.set_value('medium', r.medium);
                }
            });
        }
    },

    // ---------------------------------------------------------------
    // Helpers
    // ---------------------------------------------------------------
    copy_tracking_link: function (frm) {
        const url = frm.events.get_tracking_url(frm);
        if (navigator.clipboard) {
            navigator.clipboard.writeText(url).then(function () {
                frappe.show_alert({ message: __('Short link copied to clipboard!'), indicator: 'green' });
            });
        } else {
            const $tmp = $('<input>').val(url).appendTo('body').select();
            document.execCommand('copy');
            $tmp.remove();
            frappe.show_alert({ message: __('Short link copied!'), indicator: 'green' });
        }
    },

    get_tracking_url: function (frm) {
        return `${window.location.origin}/r/${frm.doc.short_code}`;
    }
});
