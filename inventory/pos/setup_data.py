# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _


@frappe.whitelist()
def create_default_pos_data():
    """Create default POS data for Algerian market"""
    try:
        # Create DZD currency if it doesn't exist
        create_dzd_currency()
        
        # Create default POS profile
        create_default_pos_profile()
        
        # Create sample items
        create_sample_items()
        
        frappe.db.commit()
        return {"success": True, "message": _("Default POS data created successfully")}
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Error creating default POS data: {str(e)}")
        return {"success": False, "error": str(e)}


def create_dzd_currency():
    """Create Algerian Dinar currency"""
    if not frappe.db.exists("Currency", "DZD"):
        currency = frappe.new_doc("Currency")
        currency.currency_code = "DZD"
        currency.currency_name = "Algerian Dinar"
        currency.fraction = "Centime"
        currency.fraction_units = 100
        currency.number_format = "#,###.##"
        currency.smallest_currency_fraction_value = 0.01
        currency.symbol = "د.ج"
        currency.insert(ignore_permissions=True)


def create_default_pos_profile():
    """Create a default POS profile"""
    if not frappe.db.exists("POS Profile", "Main Store"):
        pos_profile = frappe.new_doc("POS Profile")
        pos_profile.profile_name = "Main Store"
        pos_profile.company_name = "My Company"
        pos_profile.warehouse_name = "Main Warehouse"
        pos_profile.currency = "DZD"
        pos_profile.is_default = 1
        pos_profile.allow_negative_stock = 0
        pos_profile.validate_stock_on_save = 1
        
        # Add payment methods
        payment_methods = [
            {"payment_method": "Cash", "is_default": 1, "allow_in_returns": 1},
            {"payment_method": "Card", "is_default": 0, "allow_in_returns": 1},
            {"payment_method": "Bank Transfer", "is_default": 0, "allow_in_returns": 0}
        ]
        
        for pm in payment_methods:
            pos_profile.append("payment_methods", pm)
        
        pos_profile.insert(ignore_permissions=True)


def create_sample_items():
    """Create sample items for demonstration"""
    sample_items = [
        {"item_code": "BREAD-001", "item_name": "خبز - Pain", "standard_rate": 25.0, "item_group": "Spice"},
        {"item_code": "MILK-001", "item_name": "حليب - Lait", "standard_rate": 80.0, "item_group": "Spice"},
        {"item_code": "WATER-001", "item_name": "ماء - Eau", "standard_rate": 35.0, "item_group": "Vinegar"},
        {"item_code": "COFFEE-001", "item_name": "قهوة - Café", "standard_rate": 150.0, "item_group": "Spice"},
        {"item_code": "SUGAR-001", "item_name": "سكر - Sucre", "standard_rate": 120.0, "item_group": "Spice"}
    ]
    
    for item_data in sample_items:
        if not frappe.db.exists("Item", item_data["item_code"]):
            item = frappe.new_doc("Item")
            item.item_code = item_data["item_code"]
            item.item_name = item_data["item_name"]
            item.item_group = item_data["item_group"]
            item.standard_rate = item_data["standard_rate"]
            item.valuation_rate = item_data["standard_rate"] * 0.8  # Cost is 80% of selling price
            item.item_type = "Purchased"
            item.is_sales_item = 1
            # Skip unit_of_measurement if UOM doctype doesn't exist
            if frappe.db.exists("DocType", "UOM"):
                item.unit_of_measurement = "Nos"
            item.disabled = 0
            item.insert(ignore_permissions=True)


@frappe.whitelist()
def get_pos_demo_data():
    """Get demo data for POS interface"""
    # Get sample items
    items = frappe.get_all(
        "Item",
        fields=["item_code", "item_name", "standard_rate", "item_group"],
        filters={"disabled": 0, "is_sales_item": 1},
        limit_page_length=20
    )
    
    # Add mock stock quantities for demo
    for item in items:
        item["available_qty"] = 100
    
    return {
        "items": items,
        "currency": "DZD",
        "currency_symbol": "د.ج"
    } 