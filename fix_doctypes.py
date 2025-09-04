#!/usr/bin/env python3
"""
Fix missing DocType Python files for TrackFlow
Run this after pulling the latest code
"""

import os
import frappe

def create_missing_doctype_files():
    """Create missing .py files for all TrackFlow DocTypes"""
    
    doctypes_path = "apps/trackflow/trackflow/trackflow/doctype"
    
    # Template for DocType Python files
    template = '''# -*- coding: utf-8 -*-
# Copyright (c) 2024, TrackFlow and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class {classname}(Document):
    pass
'''
    
    # Get all DocType directories
    if os.path.exists(doctypes_path):
        for doctype_dir in os.listdir(doctypes_path):
            if doctype_dir.startswith('__'):
                continue
                
            dir_path = os.path.join(doctypes_path, doctype_dir)
            if os.path.isdir(dir_path):
                # Convert directory name to class name
                classname = ''.join(word.capitalize() for word in doctype_dir.split('_'))
                
                # Check if .py file exists
                py_file = os.path.join(dir_path, f"{doctype_dir}.py")
                if not os.path.exists(py_file):
                    # Create the file
                    with open(py_file, 'w') as f:
                        f.write(template.format(classname=classname))
                    print(f"Created: {py_file}")
                else:
                    print(f"Exists: {py_file}")

if __name__ == "__main__":
    create_missing_doctype_files()
    print("\nDone! Now run: bench --site your-site migrate")
