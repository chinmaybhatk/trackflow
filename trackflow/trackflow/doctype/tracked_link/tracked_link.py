# Copyright (c) 2024, Chinmay Bhat and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import string
import random


class TrackedLink(Document):
    def before_insert(self):
        if not self.short_code:
            self.short_code = self.generate_short_code()

    def after_insert(self):
        """Generate QR code after the link is first created"""
        self._generate_and_save_qr()

    def on_update(self):
        """Regenerate QR if it's missing (e.g. after manual short_code reset)"""
        if not self.qr_code:
            self._generate_and_save_qr()

    def generate_short_code(self, length=6):
        """Generate a unique short code for the link"""
        chars = string.ascii_letters + string.digits
        while True:
            code = ''.join(random.choice(chars) for _ in range(length))
            if not frappe.db.exists("Tracked Link", {"short_code": code}):
                return code

    def _generate_and_save_qr(self):
        """Generate a QR code PNG for the short URL and attach it to this document."""
        try:
            import qrcode
            import io

            site_url = frappe.utils.get_url().rstrip("/")
            short_url = f"{site_url}/r/{self.short_code}"

            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            qr.add_data(short_url)
            qr.make(fit=True)

            img = qr.make_image(fill_color="#1e293b", back_color="white")

            buf = io.BytesIO()
            img.save(buf, format="PNG")
            img_content = buf.getvalue()

            filename = f"qr_{self.short_code}.png"

            # Delete any previously attached QR for this document
            old_files = frappe.get_all(
                "File",
                filters={
                    "attached_to_doctype": self.doctype,
                    "attached_to_name": self.name,
                    "attached_to_field": "qr_code",
                },
                fields=["name"],
            )
            for f in old_files:
                frappe.delete_doc("File", f.name, ignore_permissions=True, force=True)

            file_doc = frappe.get_doc(
                {
                    "doctype": "File",
                    "file_name": filename,
                    "attached_to_doctype": self.doctype,
                    "attached_to_name": self.name,
                    "attached_to_field": "qr_code",
                    "is_private": 0,
                    "content": img_content,
                    "decode": False,
                }
            )
            file_doc.save(ignore_permissions=True)

            frappe.db.set_value(
                "Tracked Link",
                self.name,
                "qr_code",
                file_doc.file_url,
                update_modified=False,
            )
            self.qr_code = file_doc.file_url

        except Exception:
            frappe.log_error(frappe.get_traceback(), "TrackFlow QR Generation Error")


@frappe.whitelist()
def regenerate_qr(name):
    """Force-regenerate the QR code for a tracked link (callable from form button)."""
    doc = frappe.get_doc("Tracked Link", name)
    # Clear existing so on_update will rebuild it
    frappe.db.set_value("Tracked Link", name, "qr_code", None, update_modified=False)
    doc.qr_code = None
    doc._generate_and_save_qr()
    return doc.qr_code


def get_permission_query_conditions(user):
    """Return permission query conditions for Tracked Link doctype"""
    if not user:
        user = frappe.session.user

    # Everyone can see tracked links
    return None
