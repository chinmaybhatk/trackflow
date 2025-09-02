import frappe
import unittest
from frappe.utils import now_datetime, add_days
from trackflow.trackflow.doctype.link_campaign.link_campaign import LinkCampaign
from trackflow.trackflow.doctype.tracked_link.tracked_link import TrackedLink

class TestTrackFlowE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test data"""
        cls.test_campaign = None
        cls.test_tracked_link = None
        cls.test_lead = None
        
    def setUp(self):
        """Run before each test"""
        frappe.db.rollback()
        
    def test_01_create_campaign(self):
        """Test creating a marketing campaign"""
        campaign = frappe.get_doc({
            "doctype": "Link Campaign",
            "campaign_name": "Test Summer Sale",
            "campaign_type": "Email",
            "status": "Active",
            "start_date": now_datetime(),
            "end_date": add_days(now_datetime(), 30),
            "budget": 5000,
            "target_conversions": 100,
            "target_revenue": 50000
        })
        campaign.insert()
        self.test_campaign = campaign.name
        
        # Verify campaign created
        self.assertTrue(frappe.db.exists("Link Campaign", self.test_campaign))
        
    def test_02_create_tracked_link(self):
        """Test creating tracked links for campaign"""
        # First create campaign
        self.test_01_create_campaign()
        
        link = frappe.get_doc({
            "doctype": "Tracked Link",
            "campaign": self.test_campaign,
            "custom_identifier": "summer-email-header",
            "destination_url": "https://example.com/summer-sale",
            "medium": "email",
            "source": "newsletter",
            "status": "Active"
        })
        link.insert()
        self.test_tracked_link = link.name
        
        # Verify short code generated
        self.assertIsNotNone(link.short_code)
        self.assertEqual(len(link.short_code), 6)
        
    def test_03_track_click_event(self):
        """Test tracking click events"""
        # Create campaign and link
        self.test_02_create_tracked_link()
        
        # Simulate click event
        click = frappe.get_doc({
            "doctype": "Click Event",
            "tracked_link": self.test_tracked_link,
            "visitor_id": "test_visitor_123",
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0 Test Browser",
            "referrer": "https://google.com",
            "click_time": now_datetime()
        })
        click.insert()
        
        # Verify click recorded
        self.assertTrue(frappe.db.exists("Click Event", click.name))
        
    def test_04_lead_attribution(self):
        """Test lead creation with attribution"""
        # Create campaign and link
        self.test_02_create_tracked_link()
        
        # Create lead with TrackFlow fields
        lead = frappe.get_doc({
            "doctype": "CRM Lead",
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "trackflow_visitor_id": "test_visitor_123",
            "trackflow_source": "newsletter",
            "trackflow_medium": "email",
            "trackflow_campaign": self.test_campaign,
            "trackflow_first_touch_date": now_datetime(),
            "trackflow_last_touch_date": now_datetime(),
            "trackflow_touch_count": 1
        })
        lead.insert()
        self.test_lead = lead.name
        
        # Verify attribution fields
        saved_lead = frappe.get_doc("CRM Lead", self.test_lead)
        self.assertEqual(saved_lead.trackflow_campaign, self.test_campaign)
        self.assertEqual(saved_lead.trackflow_source, "newsletter")
        
    def test_05_campaign_metrics(self):
        """Test campaign performance calculation"""
        # Run previous tests to create data
        self.test_04_lead_attribution()
        
        # Get campaign metrics
        campaign = frappe.get_doc("Link Campaign", self.test_campaign)
        
        # Check click tracking
        clicks = frappe.get_all("Click Event", 
            filters={"tracked_link": ["in", 
                frappe.get_all("Tracked Link", 
                    filters={"campaign": self.test_campaign}, 
                    pluck="name")
            ]})
        self.assertGreater(len(clicks), 0)
        
    def test_06_visitor_session_tracking(self):
        """Test visitor session creation and tracking"""
        session = frappe.get_doc({
            "doctype": "Visitor Session",
            "visitor_id": "test_visitor_456",
            "session_start": now_datetime(),
            "first_page": "/products",
            "referrer_source": "google",
            "device_type": "Desktop",
            "browser": "Chrome"
        })
        session.insert()
        
        # Add page views
        session.append("page_views", {
            "page_url": "/products/summer-sale",
            "view_time": now_datetime(),
            "time_on_page": 45
        })
        session.save()
        
        self.assertEqual(len(session.page_views), 1)
        
    def test_07_redirect_handling(self):
        """Test tracked link redirect URL generation"""
        link = frappe.get_doc("Tracked Link", self.test_tracked_link)
        
        # Verify redirect URL format
        expected_url = f"/r/{link.short_code}"
        self.assertIn(link.short_code, expected_url)
        
    @classmethod
    def tearDownClass(cls):
        """Clean up test data"""
        frappe.db.rollback()
