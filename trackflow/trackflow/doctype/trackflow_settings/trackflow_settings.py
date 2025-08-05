# -*- coding: utf-8 -*-
# Copyright (c) 2024, TrackFlow and contributors
# For license information, please see license.txt

import frappe
import secrets
import string
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, add_days, get_datetime


class TrackFlowSettings(Document):
	def validate(self):
		"""Validate settings before saving."""
		if self.cookie_duration < 1:
			frappe.throw(_("Cookie duration must be at least 1 day"))
		
		if self.link_expiry_days and self.link_expiry_days < 1:
			frappe.throw(_("Link expiry must be at least 1 day"))
		
		if self.default_redirect_delay < 0:
			frappe.throw(_("Redirect delay cannot be negative"))
		
		if self.enable_email_notifications and not self.notification_recipients:
			frappe.throw(_("Please specify notification recipients"))
		
		if self.enable_webhook_notifications and not self.webhook_url:
			frappe.throw(_("Please specify webhook URL"))
		
		if self.api_rate_limit < 1:
			frappe.throw(_("API rate limit must be at least 1"))

	def on_update(self):
		"""Clear cache when settings are updated."""
		frappe.clear_cache()


@frappe.whitelist()
def generate_api_key():
	"""Generate a new API key for TrackFlow."""
	frappe.only_for("TrackFlow Manager", "System Manager")
	
	# Generate secure random key
	key_length = 32
	characters = string.ascii_letters + string.digits
	api_key = 'tf_' + ''.join(secrets.choice(characters) for _ in range(key_length))
	
	# Get settings to check expiry
	settings = frappe.get_single("TrackFlow Settings")
	expiry_date = None
	if settings.api_keys_expiry_days:
		expiry_date = add_days(now_datetime(), settings.api_keys_expiry_days)
	
	# Create API key document
	api_key_doc = frappe.new_doc("TrackFlow API Key")
	api_key_doc.key_name = f"API Key - {frappe.session.user} - {now_datetime().strftime('%Y-%m-%d %H:%M')}"
	api_key_doc.api_key = api_key
	api_key_doc.user = frappe.session.user
	api_key_doc.expiry_date = expiry_date
	api_key_doc.is_active = 1
	api_key_doc.insert()
	
	return api_key


@frappe.whitelist()
def test_email_notification():
	"""Send a test email notification."""
	frappe.only_for("TrackFlow Manager", "System Manager")
	
	settings = frappe.get_single("TrackFlow Settings")
	if not settings.enable_email_notifications:
		frappe.throw(_("Email notifications are not enabled"))
	
	if not settings.notification_recipients:
		frappe.throw(_("No notification recipients configured"))
	
	recipients = [email.strip() for email in settings.notification_recipients.split(',')]
	
	# Send test email
	frappe.sendmail(
		recipients=recipients,
		subject="TrackFlow Test Notification",
		message="""
		<p>This is a test notification from TrackFlow.</p>
		<p>If you received this email, your notification settings are configured correctly!</p>
		<br>
		<p><small>Sent from: {0}</small></p>
		""".format(frappe.local.site),
		reference_doctype="TrackFlow Settings",
		reference_name="TrackFlow Settings"
	)
	
	return True


@frappe.whitelist()
def clear_click_queue():
	"""Clear all pending click events from the queue."""
	frappe.only_for("TrackFlow Manager", "System Manager")
	
	count = frappe.db.count("Click Queue")
	frappe.db.sql("DELETE FROM `tabClick Queue`")
	frappe.db.commit()
	
	return count


def get_trackflow_settings():
	"""Get TrackFlow settings with caching."""
	return frappe.cache().get_value(
		"trackflow_settings",
		lambda: frappe.get_single("TrackFlow Settings")
	)


def is_bot_user_agent(user_agent):
	"""Check if the user agent is a bot."""
	if not user_agent:
		return False
	
	settings = get_trackflow_settings()
	if not settings.enable_bot_detection:
		return False
	
	# Get bot patterns
	bot_patterns = settings.bot_user_agents or ""
	bot_list = [pattern.strip().lower() for pattern in bot_patterns.split('\n') if pattern.strip()]
	
	# Check if user agent contains any bot pattern
	user_agent_lower = user_agent.lower()
	return any(bot in user_agent_lower for bot in bot_list)


def should_track_click(request=None):
	"""Check if click should be tracked based on settings."""
	settings = get_trackflow_settings()
	
	if not settings.enable_trackflow:
		return False
	
	if request and settings.enable_bot_detection:
		user_agent = request.headers.get('User-Agent', '')
		if is_bot_user_agent(user_agent):
			return False
	
	return True


def get_cookie_duration():
	"""Get cookie duration in days."""
	settings = get_trackflow_settings()
	return settings.cookie_duration or 30


def get_redirect_delay():
	"""Get default redirect delay in seconds."""
	settings = get_trackflow_settings()
	return settings.default_redirect_delay or 0
