import frappe

def execute():
    """Manually create Internal IP Range DocType - robust version"""
    
    print("🚀 Manual fix for Internal IP Range DocType")
    
    try:
        # Force create the DocType using SQL if needed
        create_internal_ip_range_forcefully()
        
        # Create TrackFlow Settings if needed
        create_trackflow_settings_safely()
        
        print("✅ Manual fix completed successfully")
        
    except Exception as e:
        print(f"❌ Manual fix failed: {str(e)}")
        # Don't raise exception to avoid blocking migration
        frappe.log_error(f"Manual fix error: {str(e)}", "TrackFlow Manual Fix")

def create_internal_ip_range_forcefully():
    """Create Internal IP Range DocType with force"""
    
    # Check if already exists
    if frappe.db.exists("DocType", "Internal IP Range"):
        print("✅ Internal IP Range already exists")
        return
    
    print("🏗️ Force creating Internal IP Range DocType...")
    
    # Method 1: Try standard creation
    try:
        doctype = frappe.new_doc("DocType")
        doctype.name = "Internal IP Range"
        doctype.module = "TrackFlow"
        doctype.istable = 1
        doctype.engine = "InnoDB"
        
        # Add required fields
        doctype.append("fields", {
            "fieldname": "ip_range",
            "fieldtype": "Data",
            "label": "IP Range",
            "reqd": 1,
            "in_list_view": 1
        })
        
        doctype.append("fields", {
            "fieldname": "description",
            "fieldtype": "Data",
            "label": "Description", 
            "in_list_view": 1
        })
        
        doctype.insert(ignore_permissions=True)
        frappe.db.commit()
        print("✅ Created via standard method")
        return
        
    except Exception as e1:
        print(f"Standard method failed: {str(e1)}")
        
        # Method 2: Direct SQL creation
        try:
            create_via_sql()
            print("✅ Created via SQL method")
            
        except Exception as e2:
            print(f"SQL method also failed: {str(e2)}")
            raise

def create_via_sql():
    """Create DocType directly via SQL"""
    
    # Insert DocType record
    frappe.db.sql("""
        INSERT INTO `tabDocType` (
            name, creation, modified, modified_by, owner, docstatus, idx,
            module, istable, engine, allow_rename, sort_field, sort_order
        ) VALUES (
            'Internal IP Range', NOW(), NOW(), 'Administrator', 'Administrator', 0, 0,
            'TrackFlow', 1, 'InnoDB', 0, 'modified', 'DESC'
        )
    """)
    
    # Insert fields
    frappe.db.sql("""
        INSERT INTO `tabDocField` (
            name, creation, modified, modified_by, owner, docstatus, idx,
            fieldname, fieldtype, label, parent, parenttype, parentfield,
            reqd, in_list_view
        ) VALUES 
        (
            'Internal IP Range-ip_range', NOW(), NOW(), 'Administrator', 'Administrator', 0, 1,
            'ip_range', 'Data', 'IP Range', 'Internal IP Range', 'DocType', 'fields',
            1, 1
        ),
        (
            'Internal IP Range-description', NOW(), NOW(), 'Administrator', 'Administrator', 0, 2,
            'description', 'Data', 'Description', 'Internal IP Range', 'DocType', 'fields',
            0, 1
        )
    """)
    
    # Create table
    frappe.db.sql("""
        CREATE TABLE IF NOT EXISTS `tabInternal IP Range` (
            name VARCHAR(140) NOT NULL PRIMARY KEY,
            creation DATETIME,
            modified DATETIME,
            modified_by VARCHAR(140),
            owner VARCHAR(140),
            docstatus INT(1) DEFAULT 0,
            idx INT(8) DEFAULT 0,
            ip_range VARCHAR(140),
            description VARCHAR(140),
            parent VARCHAR(140),
            parenttype VARCHAR(140),
            parentfield VARCHAR(140)
        )
    """)
    
    frappe.db.commit()

def create_trackflow_settings_safely():
    """Create TrackFlow Settings safely"""
    
    if frappe.db.exists("TrackFlow Settings", "TrackFlow Settings"):
        print("✅ TrackFlow Settings already exists")
        return
        
    print("🏗️ Creating TrackFlow Settings...")
    
    try:
        settings = frappe.new_doc("TrackFlow Settings")
        settings.enable_tracking = 1
        settings.auto_generate_short_codes = 1
        settings.short_code_length = 6
        settings.default_attribution_model = "Last Touch"
        settings.attribution_window_days = 30
        settings.cookie_expires_days = 365
        settings.gdpr_compliance_enabled = 1
        settings.cookie_consent_required = 1
        settings.insert(ignore_permissions=True)
        frappe.db.commit()
        print("✅ TrackFlow Settings created")
        
    except Exception as e:
        print(f"Failed to create TrackFlow Settings: {str(e)}")
        # Try minimal version
        frappe.db.sql("""
            INSERT INTO `tabTrackFlow Settings` (
                name, enable_tracking, short_code_length, 
                default_attribution_model, attribution_window_days, cookie_expires_days
            ) VALUES (
                'TrackFlow Settings', 1, 6, 'Last Touch', 30, 365
            )
        """)
        frappe.db.commit()
        print("✅ Created minimal TrackFlow Settings via SQL")