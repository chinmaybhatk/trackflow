import frappe
from frappe import _
import random
from datetime import datetime, timedelta
from trackflow.trackflow.utils import generate_visitor_id, generate_tracking_id

def create_demo_data():
    """Create demo data for TrackFlow"""
    print("Creating demo data for TrackFlow...")
    
    # Create demo campaigns
    campaigns = create_demo_campaigns()
    
    # Create tracking links
    links = create_demo_tracking_links(campaigns)
    
    # Create visitors and sessions
    visitors = create_demo_visitors()
    create_demo_sessions(visitors, campaigns)
    
    # Create conversions
    create_demo_conversions(visitors, campaigns)
    
    # Create leads and opportunities
    create_demo_leads_and_deals(visitors, campaigns)
    
    print("Demo data created successfully!")
    frappe.msgprint(_("TrackFlow demo data has been created!"), indicator="green")

def create_demo_campaigns():
    """Create demo campaigns"""
    campaigns = [
        {
            "campaign_name": "Spring Sale 2024",
            "campaign_type": "Email Marketing",
            "status": "Active",
            "start_date": frappe.utils.add_days(frappe.utils.today(), -30),
            "end_date": frappe.utils.add_days(frappe.utils.today(), 30),
            "budget_amount": 10000,
            "expected_revenue": 50000,
            "expected_conversions": 100,
            "description": "Spring promotional campaign targeting existing customers",
            "utm_source": "email",
            "utm_medium": "newsletter",
            "campaign_goals": [
                {
                    "goal_name": "Generate 100 Leads",
                    "metric": "Leads",
                    "target_value": 100,
                    "current_value": 45,
                    "goal_status": "In Progress"
                },
                {
                    "goal_name": "Achieve $50k Revenue",
                    "metric": "Revenue",
                    "target_value": 50000,
                    "current_value": 22500,
                    "goal_status": "In Progress"
                }
            ]
        },
        {
            "campaign_name": "Product Launch - AI Assistant",
            "campaign_type": "Social Media",
            "status": "Active",
            "start_date": frappe.utils.add_days(frappe.utils.today(), -15),
            "end_date": frappe.utils.add_days(frappe.utils.today(), 45),
            "budget_amount": 25000,
            "expected_revenue": 150000,
            "expected_conversions": 200,
            "description": "New product launch campaign across social media channels",
            "utm_source": "social",
            "utm_medium": "paid",
            "campaign_goals": [
                {
                    "goal_name": "500 Product Demo Signups",
                    "metric": "Form Submissions",
                    "target_value": 500,
                    "current_value": 127,
                    "goal_status": "In Progress"
                }
            ]
        },
        {
            "campaign_name": "SEO Content Campaign",
            "campaign_type": "Content Marketing",
            "status": "Active",
            "start_date": frappe.utils.add_months(frappe.utils.today(), -2),
            "end_date": frappe.utils.add_months(frappe.utils.today(), 4),
            "budget_amount": 5000,
            "expected_revenue": 30000,
            "expected_conversions": 50,
            "description": "Long-term content marketing campaign for organic growth",
            "utm_source": "google",
            "utm_medium": "organic"
        },
        {
            "campaign_name": "Black Friday 2023",
            "campaign_type": "Email Marketing",
            "status": "Completed",
            "start_date": frappe.utils.add_days(frappe.utils.today(), -120),
            "end_date": frappe.utils.add_days(frappe.utils.today(), -90),
            "budget_amount": 15000,
            "expected_revenue": 100000,
            "expected_conversions": 300,
            "actual_revenue": 125000,
            "actual_conversions": 342,
            "description": "Black Friday promotional campaign",
            "utm_source": "email",
            "utm_medium": "promo"
        }
    ]
    
    created_campaigns = []
    for campaign_data in campaigns:
        if not frappe.db.exists("Link Campaign", campaign_data["campaign_name"]):
            campaign = frappe.new_doc("Link Campaign")
            
            # Extract nested data
            goals = campaign_data.pop("campaign_goals", [])
            
            # Set main fields
            campaign.update(campaign_data)
            
            # Add goals
            for goal in goals:
                campaign.append("campaign_goals", goal)
            
            campaign.insert()
            created_campaigns.append(campaign)
            print(f"Created campaign: {campaign.campaign_name}")
    
    return created_campaigns

def create_demo_tracking_links(campaigns):
    """Create demo tracking links"""
    links_data = [
        {
            "title": "Spring Sale - Email Header",
            "campaign": campaigns[0].name,
            "destination_url": "https://example.com/spring-sale",
            "utm_parameters": {
                "utm_source": "email",
                "utm_medium": "newsletter",
                "utm_campaign": "spring-sale-2024",
                "utm_content": "header-cta"
            }
        },
        {
            "title": "Spring Sale - Email Footer",
            "campaign": campaigns[0].name,
            "destination_url": "https://example.com/spring-sale",
            "utm_parameters": {
                "utm_source": "email",
                "utm_medium": "newsletter",
                "utm_campaign": "spring-sale-2024",
                "utm_content": "footer-link"
            }
        },
        {
            "title": "AI Product - Facebook Ad",
            "campaign": campaigns[1].name,
            "destination_url": "https://example.com/ai-assistant",
            "utm_parameters": {
                "utm_source": "facebook",
                "utm_medium": "cpc",
                "utm_campaign": "ai-launch",
                "utm_content": "video-ad"
            }
        },
        {
            "title": "AI Product - LinkedIn Post",
            "campaign": campaigns[1].name,
            "destination_url": "https://example.com/ai-assistant/demo",
            "utm_parameters": {
                "utm_source": "linkedin",
                "utm_medium": "social",
                "utm_campaign": "ai-launch",
                "utm_content": "organic-post"
            }
        },
        {
            "title": "Blog - Ultimate Guide to AI",
            "campaign": campaigns[2].name,
            "destination_url": "https://example.com/blog/ultimate-guide-ai",
            "utm_parameters": {
                "utm_source": "google",
                "utm_medium": "organic",
                "utm_campaign": "content-seo"
            }
        }
    ]
    
    created_links = []
    for link_data in links_data:
        link = frappe.new_doc("Tracked Link")
        link.title = link_data["title"]
        link.campaign = link_data["campaign"]
        link.destination_url = link_data["destination_url"]
        link.tracking_id = generate_tracking_id()
        
        # Add UTM parameters
        for key, value in link_data["utm_parameters"].items():
            link.append("utm_parameters", {
                "parameter": key,
                "value": value
            })
        
        # Add some click data
        link.total_clicks = random.randint(50, 500)
        link.unique_clicks = int(link.total_clicks * random.uniform(0.6, 0.9))
        
        link.insert()
        created_links.append(link)
        print(f"Created tracking link: {link.title}")
    
    return created_links

def create_demo_visitors():
    """Create demo visitors"""
    visitors = []
    
    for i in range(100):
        visitor_id = generate_visitor_id()
        
        # Create visitor profile
        visitor = frappe.new_doc("Visitor Profile")
        visitor.visitor_id = visitor_id
        visitor.first_seen = frappe.utils.add_days(frappe.utils.today(), -random.randint(1, 60))
        visitor.last_seen = frappe.utils.add_days(visitor.first_seen, random.randint(0, 30))
        visitor.total_visits = random.randint(1, 10)
        visitor.total_page_views = visitor.total_visits * random.randint(2, 8)
        
        # Random location
        locations = [
            {"country": "United States", "city": "New York"},
            {"country": "United States", "city": "San Francisco"},
            {"country": "United Kingdom", "city": "London"},
            {"country": "Canada", "city": "Toronto"},
            {"country": "Australia", "city": "Sydney"},
            {"country": "India", "city": "Mumbai"},
            {"country": "Germany", "city": "Berlin"},
            {"country": "France", "city": "Paris"}
        ]
        
        location = random.choice(locations)
        visitor.country = location["country"]
        visitor.city = location["city"]
        
        # Device info
        devices = ["Desktop", "Mobile", "Tablet"]
        visitor.preferred_device = random.choice(devices)
        
        # Engagement score
        visitor.engagement_score = random.randint(10, 100)
        
        visitor.insert()
        visitors.append(visitor)
    
    print(f"Created {len(visitors)} demo visitors")
    return visitors

def create_demo_sessions(visitors, campaigns):
    """Create demo visitor sessions"""
    sources = ["google", "facebook", "linkedin", "direct", "email", "twitter"]
    mediums = ["organic", "cpc", "social", "email", "referral", "none"]
    
    for visitor in visitors[:50]:  # Create sessions for first 50 visitors
        num_sessions = random.randint(1, 5)
        
        for j in range(num_sessions):
            session = frappe.new_doc("Visitor Session")
            session.visitor_id = visitor.visitor_id
            session.visit_date = frappe.utils.add_days(
                visitor.first_seen, 
                random.randint(0, (visitor.last_seen - visitor.first_seen).days or 1)
            )
            session.session_duration = random.randint(30, 600)  # 30 seconds to 10 minutes
            session.page_views = random.randint(1, 10)
            session.bounce = 1 if session.page_views == 1 else 0
            
            # UTM parameters
            if random.random() > 0.3:  # 70% have UTM parameters
                session.utm_source = random.choice(sources)
                session.utm_medium = random.choice(mediums)
                
                if random.random() > 0.5 and campaigns:
                    campaign = random.choice(campaigns)
                    session.utm_campaign = campaign.name
                    session.campaign = campaign.name
            
            # Device info
            session.device_type = visitor.preferred_device
            browsers = ["Chrome", "Firefox", "Safari", "Edge"]
            session.browser = random.choice(browsers)
            
            # Operating system
            os_list = ["Windows", "macOS", "Linux", "iOS", "Android"]
            session.operating_system = random.choice(os_list)
            
            # Referrer
            if session.utm_source != "direct":
                referrers = [
                    "https://www.google.com/",
                    "https://www.facebook.com/",
                    "https://www.linkedin.com/",
                    "https://www.twitter.com/",
                    "https://partner-site.com/",
                    "https://blog.example.com/"
                ]
                session.referrer = random.choice(referrers)
            
            session.is_new_visitor = 1 if j == 0 else 0
            session.insert()
            
            # Create page views
            create_demo_page_views(session, session.page_views)
    
    print("Created demo sessions and page views")

def create_demo_page_views(session, num_views):
    """Create demo page views for a session"""
    pages = [
        {"url": "/", "title": "Home"},
        {"url": "/products", "title": "Products"},
        {"url": "/ai-assistant", "title": "AI Assistant Product"},
        {"url": "/pricing", "title": "Pricing"},
        {"url": "/about", "title": "About Us"},
        {"url": "/blog", "title": "Blog"},
        {"url": "/contact", "title": "Contact"},
        {"url": "/demo", "title": "Request Demo"},
        {"url": "/spring-sale", "title": "Spring Sale"},
        {"url": "/features", "title": "Features"}
    ]
    
    for i in range(num_views):
        page = random.choice(pages)
        
        page_view = frappe.new_doc("Page View")
        page_view.visitor_id = session.visitor_id
        page_view.session = session.name
        page_view.page_url = page["url"]
        page_view.page_title = page["title"]
        page_view.view_date = frappe.utils.add_to_date(
            session.visit_date,
            seconds=i * random.randint(30, 120)
        )
        page_view.time_on_page = random.randint(10, 300)
        
        # Page type
        if "product" in page["url"] or "ai-assistant" in page["url"]:
            page_view.page_type = "Product"
        elif "blog" in page["url"]:
            page_view.page_type = "Blog"
        elif "pricing" in page["url"]:
            page_view.page_type = "Pricing"
        else:
            page_view.page_type = "Other"
        
        page_view.insert()

def create_demo_conversions(visitors, campaigns):
    """Create demo conversions"""
    conversion_types = [
        "Page View", "Form Submission", "Lead Created", 
        "Deal Created", "Newsletter Signup", "Demo Request"
    ]
    
    for visitor in visitors[:30]:  # Create conversions for first 30 visitors
        num_conversions = random.randint(1, 3)
        
        for _ in range(num_conversions):
            conversion = frappe.new_doc("Link Conversion")
            conversion.visitor_id = visitor.visitor_id
            conversion.conversion_type = random.choice(conversion_types)
            conversion.conversion_date = frappe.utils.add_days(
                visitor.last_seen,
                random.randint(0, 7)
            )
            
            # Campaign attribution
            if campaigns and random.random() > 0.3:
                campaign = random.choice(campaigns)
                conversion.campaign = campaign.name
                conversion.utm_source = campaign.utm_source
                conversion.utm_medium = campaign.utm_medium
            
            # Additional fields based on type
            if conversion.conversion_type == "Lead Created":
                conversion.lead_name = f"Demo Lead {random.randint(1000, 9999)}"
                conversion.email_id = f"demo{random.randint(100, 999)}@example.com"
            elif conversion.conversion_type == "Deal Created":
                conversion.deal_value = random.randint(1000, 50000)
            
            conversion.insert()
    
    print("Created demo conversions")

def create_demo_leads_and_deals(visitors, campaigns):
    """Create demo leads and opportunities with attribution"""
    lead_sources = ["Email Campaign", "Website", "Social Media", "Partner Referral", "Trade Show"]
    industries = ["Technology", "Healthcare", "Finance", "Manufacturing", "Retail", "Education"]
    
    # Create leads
    leads = []
    for i in range(20):
        visitor = random.choice(visitors[:30])
        
        lead = frappe.new_doc("Lead")
        lead.first_name = f"Demo"
        lead.last_name = f"Lead{i+1}"
        lead.lead_name = f"Demo Lead {i+1}"
        lead.email_id = f"demolead{i+1}@example.com"
        lead.mobile_no = f"+1-555-{random.randint(1000, 9999):04d}"
        lead.source = random.choice(lead_sources)
        lead.industry = random.choice(industries)
        lead.company_name = f"Demo Company {random.randint(1, 100)}"
        lead.status = random.choice(["Open", "Contacted", "Qualified"])
        
        lead.insert()
        leads.append(lead)
        
        # Create lead link association
        if campaigns:
            link = frappe.new_doc("Lead Link Association")
            link.lead = lead.name
            link.lead_name = lead.lead_name
            link.visitor_id = visitor.visitor_id
            link.campaign = random.choice(campaigns).name
            link.insert()
    
    print(f"Created {len(leads)} demo leads")
    
    # Create opportunities
    opportunities = []
    for i in range(10):
        lead = random.choice(leads)
        visitor = visitors[i] if i < len(visitors) else random.choice(visitors)
        
        opp = frappe.new_doc("Opportunity")
        opp.opportunity_from = "Lead"
        opp.party_name = lead.name
        opp.title = f"Demo Opportunity - {lead.company_name}"
        opp.opportunity_type = "Sales"
        opp.status = random.choice(["Open", "Quotation", "Negotiation", "Closed"])
        opp.expected_closing = frappe.utils.add_days(frappe.utils.today(), random.randint(30, 90))
        opp.opportunity_amount = random.randint(5000, 100000)
        opp.probability = random.choice([25, 50, 75, 90])
        
        opp.insert()
        opportunities.append(opp)
        
        # Create deal link association
        if campaigns:
            link = frappe.new_doc("Deal Link Association")
            link.deal = opp.name
            link.deal_name = opp.title
            link.visitor_id = visitor.visitor_id
            link.lead = lead.name
            link.campaign = random.choice(campaigns).name
            link.insert()
            
            # Create deal attribution
            attribution = frappe.new_doc("Deal Attribution")
            attribution.deal = opp.name
            attribution.deal_name = opp.title
            attribution.campaign = link.campaign
            attribution.deal_value = opp.opportunity_amount
            attribution.attribution_model = "Last Touch"
            attribution.attribution_percentage = 100
            attribution.insert()
    
    print(f"Created {len(opportunities)} demo opportunities")
    
    return leads, opportunities

def clear_demo_data():
    """Clear all demo data"""
    doctypes = [
        "Deal Attribution",
        "Deal Link Association", 
        "Lead Link Association",
        "Link Conversion",
        "Page View",
        "Visitor Session",
        "Visitor Profile",
        "Tracked Link",
        "Link Campaign"
    ]
    
    for doctype in doctypes:
        frappe.db.delete(doctype)
        print(f"Cleared {doctype}")
    
    # Also clear demo leads and opportunities
    frappe.db.sql("DELETE FROM `tabLead` WHERE lead_name LIKE 'Demo Lead%'")
    frappe.db.sql("DELETE FROM `tabOpportunity` WHERE title LIKE 'Demo Opportunity%'")
    
    frappe.db.commit()
    print("All demo data cleared")
