import frappe
from frappe import _
from . import auth
from . import delivery_note_api
from . import master_data_api

@frappe.whitelist(allow_guest=True)
def login(*args, **kwargs):
    """Wrapper for auth.login to match REST API conventions"""
    # Add CORS headers
    frappe.local.response["Access-Control-Allow-Origin"] = "*"
    frappe.local.response["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    frappe.local.response["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Accept"
    frappe.local.response["Access-Control-Allow-Credentials"] = "true"
    
    return auth.login()

@frappe.whitelist()
def validate_token(*args, **kwargs):
    """Wrapper for auth.validate_token to match REST API conventions"""
    return auth.validate_token()

@frappe.whitelist()
def refresh_token(*args, **kwargs):
    """Wrapper for auth.refresh_token to match REST API conventions"""
    return auth.refresh_token()

# Master Data API endpoints
@frappe.whitelist()
def list_customers(*args, **kwargs):
    """Get a list of customers with optional search filter"""
    search_text = frappe.local.form_dict.get("search_text")
    limit = frappe.local.form_dict.get("limit")
    offset = frappe.local.form_dict.get("offset")
    return master_data_api.list_customers(search_text, limit, offset)

@frappe.whitelist()
def get_customer(*args, **kwargs):
    """Get detailed customer information by ID"""
    customer_id = frappe.local.form_dict.get("customer_id")
    return master_data_api.get_customer(customer_id)

@frappe.whitelist()
def list_items(*args, **kwargs):
    """Get a list of items with optional search filter"""
    search_text = frappe.local.form_dict.get("search_text")
    item_group = frappe.local.form_dict.get("item_group")
    limit = frappe.local.form_dict.get("limit")
    offset = frappe.local.form_dict.get("offset")
    return master_data_api.list_items(search_text, item_group, limit, offset)

@frappe.whitelist()
def get_item(*args, **kwargs):
    """Get detailed item information by item code"""
    item_code = frappe.local.form_dict.get("item_code")
    return master_data_api.get_item(item_code)

@frappe.whitelist()
def get_item_price(*args, **kwargs):
    """Get pricing information for an item, with optional customer-specific pricing"""
    item_code = frappe.local.form_dict.get("item_code")
    customer = frappe.local.form_dict.get("customer")
    return master_data_api.get_item_price(item_code, customer)

@frappe.whitelist()
def get_batch_list(*args, **kwargs):
    """Get list of batches for an item with available quantity"""
    item_code = frappe.local.form_dict.get("item_code")
    return master_data_api.get_batch_list(item_code)

@frappe.whitelist()
def get_stock_balance(*args, **kwargs):
    """Get stock balance for items"""
    item_code = frappe.local.form_dict.get("item_code")
    warehouse = frappe.local.form_dict.get("warehouse")
    return master_data_api.get_stock_balance(item_code, warehouse)

# Delivery Note API endpoints
@frappe.whitelist()
def list_delivery_notes(*args, **kwargs):
    """Get a list of all delivery notes"""
    return delivery_note_api.list_delivery_notes()

@frappe.whitelist()
def get_delivery_note(*args, **kwargs):
    """Get delivery note details by ID"""
    delivery_note_id = frappe.local.form_dict.get("delivery_note_id")
    return delivery_note_api.get_delivery_note(delivery_note_id)

@frappe.whitelist()
def create_delivery_note(*args, **kwargs):
    """Create a new delivery note"""
    return delivery_note_api.create_delivery_note()

@frappe.whitelist()
def update_delivery_note(*args, **kwargs):
    """Update an existing delivery note"""
    delivery_note_id = frappe.local.form_dict.get("delivery_note_id")
    return delivery_note_api.update_delivery_note(delivery_note_id)

@frappe.whitelist()
def delete_delivery_note(*args, **kwargs):
    """Delete a delivery note"""
    delivery_note_id = frappe.local.form_dict.get("delivery_note_id")
    return delivery_note_api.delete_delivery_note(delivery_note_id)

@frappe.whitelist()
def submit_delivery_note(*args, **kwargs):
    """Submit a delivery note"""
    delivery_note_id = frappe.local.form_dict.get("delivery_note_id")
    return delivery_note_api.submit_delivery_note(delivery_note_id)

@frappe.whitelist()
def cancel_delivery_note(*args, **kwargs):
    """Cancel a delivery note"""
    delivery_note_id = frappe.local.form_dict.get("delivery_note_id")
    return delivery_note_api.cancel_delivery_note(delivery_note_id)

@frappe.whitelist()
def get_delivery_notes_for_customer(*args, **kwargs):
    """Get all delivery notes for a specific customer"""
    customer_id = frappe.local.form_dict.get("customer_id")
    return delivery_note_api.get_delivery_notes_for_customer(customer_id)

@frappe.whitelist()
def get_delivery_note_items_from_sales_order(*args, **kwargs):
    """Get items from a sales order to create a delivery note"""
    sales_order_id = frappe.local.form_dict.get("sales_order_id")
    return delivery_note_api.get_delivery_note_items_from_sales_order(sales_order_id)

# Reference data API endpoints
@frappe.whitelist()
def get_uoms(*args, **kwargs):
    """Get list of all UOMs (Units of Measurement)"""
    return master_data_api.get_uoms()

@frappe.whitelist()
def get_brands(*args, **kwargs):
    """Get list of all unique brands from items"""
    return master_data_api.get_brands()

# Define more API endpoints here as needed

