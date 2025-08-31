import frappe

def after_install():
    """
    Set up initial data after app installation
    """
    setup_inventory_settings()

def setup_inventory_settings():
    """
    Create the Inventory Settings doctype with default values
    """
    # Check if Inventory Settings already exists
    if not frappe.db.exists("DocType", "Inventory Settings"):
        frappe.msgprint("Inventory Settings DocType not found. Please reinstall the app or manually create it.")
        return
    
    # Check if a settings document exists already
    if frappe.db.exists("Inventory Settings", "Inventory Settings"):
        return
    
    # Find a default warehouse to use
    default_warehouse = None
    warehouses = frappe.get_all("Warehouse", limit=1)
    if warehouses:
        default_warehouse = warehouses[0].name
    
    # Create the settings
    doc = frappe.new_doc("Inventory Settings")
    doc.enable_perpetual_inventory = 1
    
    if default_warehouse:
        doc.default_warehouse = default_warehouse
    
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    
    if not default_warehouse:
        frappe.msgprint("No warehouse found. Please create a warehouse and set it as the default in Inventory Settings.") 