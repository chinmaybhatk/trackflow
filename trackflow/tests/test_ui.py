import os
from playwright.sync_api import sync_playwright
import pytest

class TestTrackFlowUI:
    """UI automation tests for TrackFlow using Playwright"""
    
    @pytest.fixture(scope="class")
    def browser_context(self):
        """Setup browser context with login"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            
            # Login to Frappe
            page.goto(os.environ.get('FRAPPE_URL', 'http://localhost:8000'))
            page.fill('input[name="usr"]', os.environ.get('TEST_USER', 'Administrator'))
            page.fill('input[name="pwd"]', os.environ.get('TEST_PASSWORD', 'admin'))
            page.click('button[type="submit"]')
            page.wait_for_url('**/app')
            
            yield context
            browser.close()
    
    def test_create_campaign_ui(self, browser_context):
        """Test creating campaign through UI"""
        page = browser_context.new_page()
        
        # Navigate to Link Campaign
        page.goto(f"{os.environ.get('FRAPPE_URL')}/app/link-campaign")
        page.click('button:has-text("Add Link Campaign")')
        
        # Fill campaign form
        page.fill('input[data-fieldname="campaign_name"]', 'UI Test Campaign')
        page.select_option('select[data-fieldname="campaign_type"]', 'Social Media')
        page.select_option('select[data-fieldname="status"]', 'Active')
        page.fill('input[data-fieldname="budget"]', '10000')
        
        # Save
        page.click('button:has-text("Save")')
        page.wait_for_selector('.msgprint:has-text("Saved")')
        
        # Verify
        assert page.locator('h3:has-text("UI Test Campaign")').is_visible()
        
    def test_generate_tracked_link(self, browser_context):
        """Test generating tracked link"""
        page = browser_context.new_page()
        
        # Create tracked link
        page.goto(f"{os.environ.get('FRAPPE_URL')}/app/tracked-link")
        page.click('button:has-text("Add Tracked Link")')
        
        # Fill form
        page.fill('input[data-fieldname="custom_identifier"]', 'ui-test-link')
        page.fill('input[data-fieldname="destination_url"]', 'https://example.com/test')
        page.fill('input[data-fieldname="medium"]', 'email')
        page.fill('input[data-fieldname="source"]', 'newsletter')
        
        # Link to campaign
        page.click('input[data-fieldname="campaign"]')
        page.fill('input[data-fieldname="campaign"]', 'UI Test Campaign')
        page.keyboard.press('Enter')
        
        # Save
        page.click('button:has-text("Save")')
        page.wait_for_selector('.msgprint:has-text("Saved")')
        
        # Check short code generated
        short_code = page.locator('input[data-fieldname="short_code"]').input_value()
        assert len(short_code) == 6
        
    def test_view_analytics(self, browser_context):
        """Test viewing analytics dashboard"""
        page = browser_context.new_page()
        
        # Navigate to Click Events
        page.goto(f"{os.environ.get('FRAPPE_URL')}/app/click-event")
        
        # Check list view
        assert page.locator('.list-row').count() >= 0
        
        # Apply filters
        page.click('button:has-text("Filter")')
        page.wait_for_timeout(500)
        
        # Test date filter
        page.click('[data-fieldname="click_time"] input')
        page.keyboard.type('2025-01-01')
        page.click('button:has-text("Apply")')
        
    def test_lead_attribution_fields(self, browser_context):
        """Test TrackFlow fields in CRM Lead"""
        page = browser_context.new_page()
        
        # Create new lead
        page.goto(f"{os.environ.get('FRAPPE_URL')}/app/lead")
        page.click('button:has-text("Add Lead")')
        
        # Fill basic info
        page.fill('input[data-fieldname="first_name"]', 'Test')
        page.fill('input[data-fieldname="last_name"]', 'Lead')
        page.fill('input[data-fieldname="email_id"]', 'test@example.com')
        
        # Check TrackFlow tab exists
        page.click('a:has-text("TrackFlow")')
        
        # Verify fields
        assert page.locator('input[data-fieldname="trackflow_visitor_id"]').is_visible()
        assert page.locator('input[data-fieldname="trackflow_source"]').is_visible()
        assert page.locator('input[data-fieldname="trackflow_medium"]').is_visible()

# Run with: pytest trackflow/tests/test_ui.py -v
