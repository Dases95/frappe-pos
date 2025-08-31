import frappe

def execute():
    """
    Migrate Price List doctype data to Item Price doctype
    This script should be run after updating the Item Price doctype schema
    """
    frappe.flags.in_migrate = True

    # Step 1: Update existing Item Price records with price_list_name
    item_prices = frappe.get_all("Item Price", 
                               fields=["name", "price_list"])
    
    for item_price in item_prices:
        if item_price.price_list:
            # Get price list details
            try:
                price_list_doc = frappe.get_doc("Price List", item_price.price_list)
                
                # Update item price with price list details
                frappe.db.set_value("Item Price", item_price.name, {
                    "price_list_name": price_list_doc.price_list_name,
                    "buying": price_list_doc.buying,
                    "selling": price_list_doc.selling,
                    "currency": price_list_doc.currency,
                    "enabled": price_list_doc.enabled
                })
                
                print(f"Updated Item Price {item_price.name} with Price List {price_list_doc.price_list_name}")
            except Exception as e:
                print(f"Error updating Item Price {item_price.name}: {e}")
    
    # Step 2: Update any document types that reference price_list field
    # Example: If you have other doctypes that reference Price List, update those references
    
    # Step 3: Remove the price_list field from Item Price doctype
    # This should be done manually after confirming migration success
    
    print("Price List migration completed. Please review and test before removing the Price List doctype.")
    
    frappe.flags.in_migrate = False

def create_example_party_specific_pricing():
    """Create example party-specific pricing for demonstration"""
    
    try:
        # Check if we have any items to work with
        items = frappe.get_all("Item", filters={"disabled": 0}, limit=2)
        if not items or len(items) == 0:
            return
        
        # Get a selling price list
        selling_price_list = frappe.get_all("Price List", 
                                           filters={"selling": 1, "enabled": 1}, 
                                           limit=1)
        if not selling_price_list:
            return
            
        # Get a buying price list
        buying_price_list = frappe.get_all("Price List", 
                                          filters={"buying": 1, "enabled": 1}, 
                                          limit=1)
        if not buying_price_list:
            return
            
        # Check if we have customers and suppliers
        customers = frappe.get_all("Customer", limit=1)
        suppliers = frappe.get_all("Supplier", limit=1)
        
        # Try to create customer-specific pricing
        if customers and len(customers) > 0:
            customer = customers[0].name
            try:
                # Get existing price for the item
                existing_price = frappe.get_all(
                    "Item Price",
                    filters={"item_code": items[0].name, "selling": 1},
                    fields=["price_list_rate"],
                    limit=1
                )
                
                # Create a special price for this customer (10% discount)
                if existing_price and len(existing_price) > 0:
                    special_rate = existing_price[0].price_list_rate * 0.9
                    
                    doc = frappe.get_doc({
                        "doctype": "Item Price",
                        "item_code": items[0].name,
                        "price_list": selling_price_list[0].name,
                        "price_list_rate": special_rate,
                        "customer": customer,
                        "selling": 1,
                        "buying": 0,
                        "valid_from": frappe.utils.today(),
                        "uom": frappe.db.get_value("Item", items[0].name, "unit_of_measurement") or "Nos"
                    })
                    doc.insert()
                    frappe.db.commit()
                    frappe.msgprint(f"Created example customer-specific pricing for {items[0].name}")
            except Exception as e:
                frappe.log_error(f"Failed to create customer-specific pricing: {str(e)}", 
                               "Price List Migration Error")
                
        # Try to create supplier-specific pricing
        if suppliers and len(suppliers) > 0:
            supplier = suppliers[0].name
            try:
                # Get existing price for the item
                existing_price = frappe.get_all(
                    "Item Price",
                    filters={"item_code": items[0].name, "buying": 1},
                    fields=["price_list_rate"],
                    limit=1
                )
                
                # Create a special price from this supplier (5% discount)
                if existing_price and len(existing_price) > 0:
                    special_rate = existing_price[0].price_list_rate * 0.95
                    
                    doc = frappe.get_doc({
                        "doctype": "Item Price",
                        "item_code": items[0].name,
                        "price_list": buying_price_list[0].name,
                        "price_list_rate": special_rate,
                        "supplier": supplier,
                        "selling": 0,
                        "buying": 1,
                        "valid_from": frappe.utils.today(),
                        "uom": frappe.db.get_value("Item", items[0].name, "unit_of_measurement") or "Nos"
                    })
                    doc.insert()
                    frappe.db.commit()
                    frappe.msgprint(f"Created example supplier-specific pricing for {items[0].name}")
            except Exception as e:
                frappe.log_error(f"Failed to create supplier-specific pricing: {str(e)}", 
                               "Price List Migration Error")
    except Exception as e:
        frappe.log_error(f"Failed to create example party-specific pricing: {str(e)}", 
                       "Price List Migration Error")

if __name__ == "__main__":
    execute() 