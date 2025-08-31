#!/usr/bin/env python3
"""
Setup script to create default POS shortcuts
Run this script to create initial shortcuts for the POS system
"""

import frappe
from frappe import _

def create_default_shortcuts():
    """Create default shortcuts for POS system"""
    
    # Check if shortcuts already exist
    existing_shortcuts = frappe.get_all("POS Shortcut", fields=["shortcut_key"])
    existing_keys = [s.shortcut_key for s in existing_shortcuts]
    
    default_shortcuts = [
        # Function shortcuts
        {
            "shortcut_name": "New Sale",
            "shortcut_type": "Function",
            "shortcut_key": "F1",
            "action_type": "New Sale",
            "is_active": 1
        },
        {
            "shortcut_name": "Clear Cart",
            "shortcut_type": "Function",
            "shortcut_key": "F2",
            "action_type": "Clear Cart",
            "is_active": 1
        },
        {
            "shortcut_name": "Print Receipt",
            "shortcut_type": "Function",
            "shortcut_key": "F3",
            "action_type": "Print Receipt",
            "is_active": 1
        },
        {
            "shortcut_name": "Close Session",
            "shortcut_type": "Function",
            "shortcut_key": "F4",
            "action_type": "Close Session",
            "is_active": 1
        },
        {
            "shortcut_name": "Toggle Language",
            "shortcut_type": "Function",
            "shortcut_key": "F5",
            "action_type": "Toggle Language",
            "is_active": 1
        },
        
        # Payment shortcuts
        {
            "shortcut_name": "Cash",
            "shortcut_type": "Payment",
            "shortcut_key": "1",
            "is_active": 1
        },
        {
            "shortcut_name": "Card",
            "shortcut_type": "Payment",
            "shortcut_key": "2",
            "is_active": 1
        },
        {
            "shortcut_name": "Bank Transfer",
            "shortcut_type": "Payment",
            "shortcut_key": "3",
            "is_active": 1
        },
        
        # Product shortcuts (will be populated with actual items)
        {
            "shortcut_name": "Quick Item 1",
            "shortcut_type": "Product",
            "shortcut_key": "4",
            "item_code": "خل",
            "item_name": "خل المنتج",
            "is_active": 1
        },
        {
            "shortcut_name": "Quick Item 2",
            "shortcut_type": "Product",
            "shortcut_key": "5",
            "item_code": "dqsd",
            "item_name": "dqd",
            "is_active": 1
        },
        {
            "shortcut_name": "Quick Item 3",
            "shortcut_type": "Product",
            "shortcut_key": "6",
            "item_code": "0212",
            "item_name": "فلفل اسود",
            "is_active": 1
        }
    ]
    
    created_count = 0
    for shortcut_data in default_shortcuts:
        if shortcut_data["shortcut_key"] not in existing_keys:
            try:
                shortcut = frappe.new_doc("POS Shortcut")
                shortcut.update(shortcut_data)
                shortcut.insert()
                created_count += 1
                print(f"Created shortcut: {shortcut_data['shortcut_name']} ({shortcut_data['shortcut_key']})")
            except Exception as e:
                print(f"Error creating shortcut {shortcut_data['shortcut_name']}: {e}")
        else:
            print(f"Shortcut {shortcut_data['shortcut_name']} already exists")
    
    print(f"\nCreated {created_count} new shortcuts")
    print("POS shortcuts setup completed!")

if __name__ == "__main__":
    create_default_shortcuts() 