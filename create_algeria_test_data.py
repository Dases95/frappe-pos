#!/usr/bin/env python3
"""
Algeria Test Data Creator

This script creates comprehensive test data for the Algerian market.
Run this script from the frappe-bench directory.

Usage:
    python apps/inventory/create_algeria_test_data.py --site your-site-name
    python apps/inventory/create_algeria_test_data.py --site your-site-name --customers 100 --suppliers 30
"""

import os
import sys
import argparse

# Add the current directory to Python path
sys.path.insert(0, '.')

import frappe
from frappe.utils import flt, add_days, today
import random

# Import the test data functions
from apps.inventory.inventory.commands.test_data import (
    create_test_customers,
    create_test_suppliers, 
    create_test_items,
    create_test_warehouses,
    create_test_transactions,
    ALGERIAN_PRODUCTS
)

def main():
    parser = argparse.ArgumentParser(description='Create Algeria test data')
    parser.add_argument('--site', required=True, help='Site name')
    parser.add_argument('--customers', type=int, default=50, help='Number of customers to create')
    parser.add_argument('--suppliers', type=int, default=20, help='Number of suppliers to create')
    parser.add_argument('--items', type=int, default=None, help='Number of items to create (default: all predefined items)')
    parser.add_argument('--transactions', type=int, default=100, help='Number of transactions to create')
    parser.add_argument('--clear', action='store_true', help='Clear existing test data first')
    
    args = parser.parse_args()
    
    # Initialize Frappe
    frappe.init(site=args.site)
    frappe.connect()
    
    print(f"Creating Algeria test data for site: {args.site}")
    print("=" * 50)
    
    try:
        if args.clear:
            print("Clearing existing test data...")
            clear_test_data()
        
        # Create basic master data
        create_test_warehouses()
        create_test_items(args.items)
        create_test_customers(args.customers)
        create_test_suppliers(args.suppliers)
        
        # Create transactions
        create_test_transactions(args.transactions)
        
        frappe.db.commit()
        print("=" * 50)
        print("✅ Algeria test data creation completed successfully!")
        print(f"Created:")
        print(f"  - {args.customers} customers")
        print(f"  - {args.suppliers} suppliers")
        print(f"  - {len(ALGERIAN_PRODUCTS) if args.items is None else args.items} items")
        print(f"  - 8 warehouses")
        print(f"  - {args.transactions} transactions")
        
    except Exception as e:
        frappe.db.rollback()
        print(f"❌ Error creating test data: {e}")
        raise
    finally:
        frappe.destroy()

def clear_test_data():
    """Clear all test data"""
    doctypes_to_clear = [
        "Sales Order", "Purchase Order", "Delivery Note", "Purchase Receipt",
        "Stock Entry", "Stock Ledger Entry", "Item Price",
        "Item", "Customer", "Supplier", "Warehouse", "Item Group"
    ]
    
    for doctype in doctypes_to_clear:
        try:
            count = frappe.db.count(doctype)
            if count > 0:
                frappe.db.sql(f"DELETE FROM `tab{doctype}`")
                print(f"Deleted {count} {doctype} records")
        except Exception as e:
            print(f"Warning: Could not clear {doctype}: {e}")

if __name__ == '__main__':
    main()