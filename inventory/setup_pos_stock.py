#!/usr/bin/env python3
"""
Setup script to fix POS stock update issues
This script ensures:
1. At least one warehouse exists
2. Inventory Settings document is created with default warehouse
3. Stock updates work properly in POS
"""

import frappe
from frappe import _

def setup_pos_stock_system():
    """
    Main setup function to fix POS stock update issues
    """
    print("Setting up POS stock system...")
    
    # Step 1: Ensure at least one warehouse exists
    warehouse = ensure_warehouse_exists()
    
    # Step 2: Setup Inventory Settings with default warehouse
    setup_inventory_settings_with_warehouse(warehouse)
    
    # Step 3: Verify the setup
    verify_setup()
    
    print("POS stock system setup completed successfully!")

def ensure_warehouse_exists():
    """
    Ensure at least one warehouse exists, create one if none exist
    """
    print("Checking for existing warehouses...")
    
    # Check if any warehouse exists
    warehouses = frappe.get_all("Warehouse", limit=1)
    
    if warehouses:
        warehouse_name = warehouses[0].name
        print(f"Found existing warehouse: {warehouse_name}")
        return warehouse_name
    
    # Create a default warehouse if none exists
    print("No warehouse found. Creating default warehouse...")
    
    warehouse_doc = frappe.new_doc("Warehouse")
    warehouse_doc.warehouse_name = "Main Warehouse"
    warehouse_doc.warehouse_code = "MAIN"
    warehouse_doc.warehouse_type = "Finished Goods"
    warehouse_doc.address = "Default warehouse for POS operations"
    warehouse_doc.is_active = 1
    
    try:
        warehouse_doc.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"Created warehouse: {warehouse_doc.name}")
        return warehouse_doc.name
    except Exception as e:
        print(f"Error creating warehouse: {str(e)}")
        frappe.throw(_("Failed to create default warehouse: {0}").format(str(e)))

def setup_inventory_settings_with_warehouse(warehouse_name):
    """
    Setup Inventory Settings document with the specified warehouse
    """
    print("Setting up Inventory Settings...")
    
    # Check if Inventory Settings document already exists
    if frappe.db.exists("Inventory Settings", "Inventory Settings"):
        # Update existing settings
        settings_doc = frappe.get_doc("Inventory Settings", "Inventory Settings")
        if not settings_doc.default_warehouse:
            settings_doc.default_warehouse = warehouse_name
            settings_doc.save(ignore_permissions=True)
            frappe.db.commit()
            print(f"Updated Inventory Settings with default warehouse: {warehouse_name}")
        else:
            print(f"Inventory Settings already configured with warehouse: {settings_doc.default_warehouse}")
    else:
        # Create new Inventory Settings document
        settings_doc = frappe.new_doc("Inventory Settings")
        settings_doc.default_warehouse = warehouse_name
        settings_doc.enable_perpetual_inventory = 1
        settings_doc.automatically_set_serial_nos = 0
        settings_doc.auto_create_batch = 0
        
        try:
            settings_doc.insert(ignore_permissions=True)
            frappe.db.commit()
            print(f"Created Inventory Settings with default warehouse: {warehouse_name}")
        except Exception as e:
            print(f"Error creating Inventory Settings: {str(e)}")
            frappe.throw(_("Failed to create Inventory Settings: {0}").format(str(e)))

def verify_setup():
    """
    Verify that the setup is correct
    """
    print("Verifying setup...")
    
    # Check if Inventory Settings exists and has default warehouse
    if not frappe.db.exists("Inventory Settings", "Inventory Settings"):
        frappe.throw(_("Inventory Settings document not found after setup"))
    
    settings = frappe.get_doc("Inventory Settings", "Inventory Settings")
    if not settings.default_warehouse:
        frappe.throw(_("Default warehouse not set in Inventory Settings"))
    
    # Check if the warehouse exists
    if not frappe.db.exists("Warehouse", settings.default_warehouse):
        frappe.throw(_("Default warehouse {0} does not exist").format(settings.default_warehouse))
    
    print(f"✓ Inventory Settings configured with warehouse: {settings.default_warehouse}")
    print(f"✓ Warehouse {settings.default_warehouse} exists and is accessible")
    print("✓ POS stock update system is properly configured")

def run_setup():
    """
    Entry point to run the setup
    """
    try:
        setup_pos_stock_system()
        return {"status": "success", "message": "POS stock system setup completed successfully"}
    except Exception as e:
        error_msg = f"Setup failed: {str(e)}"
        print(error_msg)
        frappe.log_error(error_msg, "POS Stock Setup Error")
        return {"status": "error", "message": error_msg}

if __name__ == "__main__":
    # This allows the script to be run directly
    setup_pos_stock_system()