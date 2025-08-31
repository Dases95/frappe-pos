import frappe
from frappe import _
from frappe.utils import cint, flt

@frappe.whitelist()
def list_customers(search_text=None, limit=20, offset=0):
    """
    Get a list of customers with optional search filter
    
    Args:
        search_text (str, optional): Search text to filter customers by name or ID
        limit (int, optional): Limit number of results (default: 20)
        offset (int, optional): Offset for pagination (default: 0)
        
    Returns:
        dict: List of customers
    """
    try:
        # Convert limit and offset to integers with defaults
        limit = cint(limit) or 20
        offset = cint(offset) or 0
        
        # Build filters
        filters = {"status": "Active"}
        
        # Add search filter if provided
        if search_text:
            filters.update({
                "name": ["like", f"%{search_text}%"]
            })
        
        # Get customers
        customers = frappe.get_all(
            "Customer",
            filters=filters,
            fields=["name", "customer_name", "customer_type", "contact_number", "email", "wilaya", "commune"],
            limit=limit,
            start=offset,
            order_by="customer_name asc"
        )
        
        # Get total count for pagination
        total_count = frappe.db.count("Customer", filters=filters)
        
        return {
            "success": True,
            "data": customers,
            "total": total_count,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        frappe.log_error(f"Error in list_customers: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to retrieve customers: {str(e)}"
        }

@frappe.whitelist()
def get_customer(customer_id):
    """
    Get detailed customer information by ID
    
    Args:
        customer_id (str): The customer ID
        
    Returns:
        dict: Customer details
    """
    try:
        if not customer_id:
            return {
                "success": False,
                "message": "Customer ID is required"
            }
        
        # Get customer document
        customer = frappe.get_doc("Customer", customer_id)
        
        # Convert to dict for API response
        customer_dict = customer.as_dict()
        
        # Format address for easy display
        full_address = []
        if customer.address:
            full_address.append(customer.address)
        
        if customer.commune:
            commune_name = frappe.db.get_value("Commune", customer.commune, "commune_name")
            if commune_name:
                full_address.append(f"Commune: {commune_name}")
        
        if customer.wilaya:
            wilaya_name = frappe.db.get_value("Wilaya", customer.wilaya, "wilaya_name")
            if wilaya_name:
                full_address.append(f"Wilaya: {wilaya_name}")
        
        # Add formatted address to response
        customer_dict["full_address"] = ", ".join(full_address) if full_address else ""
        
        return {
            "success": True,
            "data": customer_dict
        }
    except frappe.DoesNotExistError:
        return {
            "success": False,
            "message": f"Customer {customer_id} not found"
        }
    except Exception as e:
        frappe.log_error(f"Error in get_customer: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to retrieve customer: {str(e)}"
        }

@frappe.whitelist()
def list_items(search_text=None, item_group=None, limit=20, offset=0):
    """
    Get a list of items with optional search filter
    
    Args:
        search_text (str, optional): Search text to filter items by name or code
        item_group (str, optional): Filter by item group
        limit (int, optional): Limit number of results (default: 20)
        offset (int, optional): Offset for pagination (default: 0)
        
    Returns:
        dict: List of items
    """
    try:
        # Convert limit and offset to integers with defaults
        limit = cint(limit) or 20
        offset = cint(offset) or 0
        
        # Build filters
        filters = {}
        
        # Add item group filter if provided
        if item_group:
            filters["item_group"] = item_group
        
        # Add search filter if provided
        if search_text:
            filters.update([
                [
                    "Item",
                    "name",
                    "like",
                    f"%{search_text}%"
                ],
                [
                    "Item",
                    "item_name",
                    "like",
                    f"%{search_text}%"
                ]
            ])
        
        # Get items - MODIFIED: removed non-existent fields
        items = frappe.get_all(
            "Item",
            filters=filters,
            fields=[
                "name as item_code", 
                "item_name", 
                "description", 
                "item_group", 
                "unit_of_measurement as uom", 
                "disabled",
                "batch_tracking"
            ],
            limit=limit,
            start=offset,
            order_by="item_name asc"
        )
        
        # Get the default price for each item
        for item in items:
            # Get default selling price
            default_price = frappe.db.get_value(
                "Item Price",
                {
                    "item_code": item.item_code,
                    "selling": 1,
                    "is_default_price": 1
                },
                "price_list_rate"
            )
            
            item.default_price = flt(default_price) if default_price else 0
            
            # Get available stock (sum of actual quantity from Stock Ledger)
            stock_qty = frappe.db.sql("""
                SELECT SUM(actual_qty) 
                FROM `tabStock Ledger Entry` 
                WHERE item = %s AND is_cancelled = 0
            """, item.item_code)[0][0]
            
            item.available_qty = flt(stock_qty) if stock_qty else 0
        
        # Get total count for pagination
        total_count = frappe.db.count("Item", filters=filters)
        
        return {
            "success": True,
            "data": items,
            "total": total_count,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        frappe.log_error(f"Error in list_items: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to retrieve items: {str(e)}"
        }

@frappe.whitelist()
def get_item(item_code):
    """
    Get detailed item information by item code
    
    Args:
        item_code (str): The item code
        
    Returns:
        dict: Item details
    """
    try:
        if not item_code:
            return {
                "success": False,
                "message": "Item code is required"
            }
        
        # Get item document
        item = frappe.get_doc("Item", item_code)
        
        # Convert to dict for API response
        item_dict = item.as_dict()
        
        # Add price information
        # Get default selling price
        default_price = frappe.db.get_value(
            "Item Price",
            {
                "item_code": item_code,
                "selling": 1,
                "is_default_price": 1
            },
            "price_list_rate"
        )
        
        item_dict["default_price"] = flt(default_price) if default_price else 0
        
        # Get all selling prices
        selling_prices = frappe.get_all(
            "Item Price",
            filters={
                "item_code": item_code,
                "selling": 1
            },
            fields=["name", "price_list_rate", "customer", "valid_from", "valid_upto"]
        )
        
        item_dict["selling_prices"] = selling_prices or []
        
        # Get available stock (sum of actual quantity from Stock Ledger)
        stock_qty = frappe.db.sql("""
            SELECT SUM(actual_qty) 
            FROM `tabStock Ledger Entry` 
            WHERE item = %s AND is_cancelled = 0
        """, item_code)[0][0]
        
        item_dict["available_qty"] = flt(stock_qty) if stock_qty else 0
        
        # If batch tracking is enabled, get batch information
        if item.batch_tracking:
            batches = frappe.db.sql("""
                SELECT b.name, b.batch_number, b.manufacturing_date, b.expiry_date,
                SUM(sle.actual_qty) as qty
                FROM `tabBatch` b
                JOIN `tabStock Ledger Entry` sle ON sle.batch = b.name
                WHERE sle.item = %s AND sle.is_cancelled = 0
                GROUP BY b.name
                HAVING SUM(sle.actual_qty) > 0
                ORDER BY b.expiry_date
            """, item_code, as_dict=1)
            
            item_dict["batches"] = batches or []
        
        return {
            "success": True,
            "data": item_dict
        }
    except frappe.DoesNotExistError:
        return {
            "success": False,
            "message": f"Item {item_code} not found"
        }
    except Exception as e:
        frappe.log_error(f"Error in get_item: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to retrieve item: {str(e)}"
        }

@frappe.whitelist()
def get_item_price(item_code, customer=None):
    """
    Get pricing information for an item, with optional customer-specific pricing
    
    Args:
        item_code (str): The item code
        customer (str, optional): The customer ID for customer-specific pricing
        
    Returns:
        dict: Item pricing details
    """
    try:
        if not item_code:
            return {
                "success": False,
                "message": "Item code is required"
            }
        
        result = {
            "item_code": item_code,
            "default_price": 0,
            "customer_price": 0,
            "has_customer_specific_price": False
        }
        
        # Get default selling price
        default_price = frappe.db.get_value(
            "Item Price",
            {
                "item_code": item_code,
                "selling": 1,
                "is_default_price": 1
            },
            "price_list_rate"
        )
        
        result["default_price"] = flt(default_price) if default_price else 0
        
        # If customer is provided, get customer-specific price
        if customer:
            customer_price = frappe.db.get_value(
                "Item Price",
                {
                    "item_code": item_code,
                    "selling": 1,
                    "customer": customer
                },
                "price_list_rate"
            )
            
            if customer_price:
                result["customer_price"] = flt(customer_price)
                result["has_customer_specific_price"] = True
        
        # If no customer-specific price, use default price
        if not result["has_customer_specific_price"]:
            result["customer_price"] = result["default_price"]
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        frappe.log_error(f"Error in get_item_price: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to retrieve item price: {str(e)}"
        }

@frappe.whitelist()
def get_batch_list(item_code):
    """
    Get list of batches for an item with available quantity
    
    Args:
        item_code (str): The item code
        
    Returns:
        dict: List of batches with available quantity
    """
    try:
        if not item_code:
            return {
                "success": False,
                "message": "Item code is required"
            }
        
        # Check if item has batch tracking
        has_batch_tracking = frappe.db.get_value("Item", item_code, "batch_tracking")
        
        if not has_batch_tracking:
            return {
                "success": False,
                "message": f"Item {item_code} does not have batch tracking enabled"
            }
        
        # Get batches with available quantity
        batches = frappe.db.sql("""
            SELECT b.name, b.batch_number, b.manufacturing_date, b.expiry_date,
            SUM(sle.actual_qty) as available_qty
            FROM `tabBatch` b
            JOIN `tabStock Ledger Entry` sle ON sle.batch = b.name
            WHERE sle.item = %s AND sle.is_cancelled = 0
            GROUP BY b.name
            HAVING SUM(sle.actual_qty) > 0
            ORDER BY b.expiry_date
        """, item_code, as_dict=1)
        
        return {
            "success": True,
            "data": batches or []
        }
    except Exception as e:
        frappe.log_error(f"Error in get_batch_list: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to retrieve batch list: {str(e)}"
        }

@frappe.whitelist()
def get_stock_balance(item_code=None, warehouse=None):
    """
    Get stock balance for items
    
    Args:
        item_code (str, optional): Filter by specific item
        warehouse (str, optional): Filter by specific warehouse
        
    Returns:
        dict: Stock balance information
    """
    try:
        # Build filters
        filters = {"is_cancelled": 0}
        
        if item_code:
            filters["item"] = item_code
        
        if warehouse:
            filters["warehouse"] = warehouse
        
        # Group by item to get total quantity
        stock_balance = frappe.db.sql("""
            SELECT 
                sle.item, 
                i.item_name,
                i.unit_of_measurement as uom,
                SUM(sle.actual_qty) as available_qty
            FROM 
                `tabStock Ledger Entry` sle
            JOIN
                `tabItem` i ON sle.item = i.name
            WHERE 
                sle.is_cancelled = %(is_cancelled)s
                {item_condition}
                {warehouse_condition}
            GROUP BY 
                sle.item, i.item_name, i.unit_of_measurement
            HAVING 
                SUM(sle.actual_qty) != 0
            ORDER BY 
                i.item_name
        """.format(
            item_condition=f"AND sle.item = %(item)s" if item_code else "",
            warehouse_condition=f"AND sle.warehouse = %(warehouse)s" if warehouse else ""
        ), filters, as_dict=1)
        
        return {
            "success": True,
            "data": stock_balance or []
        }
    except Exception as e:
        frappe.log_error(f"Error in get_stock_balance: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to retrieve stock balance: {str(e)}"
        }

@frappe.whitelist()
def get_uoms():
    """
    Get list of all UOMs (Units of Measurement)
    
    Returns:
        dict: List of UOMs
    """
    try:
        uoms = frappe.get_all(
            "UOM",
            fields=["name", "uom_name"],
            order_by="uom_name asc"
        )
        
        return {
            "success": True,
            "data": uoms
        }
    except Exception as e:
        frappe.log_error(f"Error in get_uoms: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to retrieve UOMs: {str(e)}"
        }

@frappe.whitelist()
def get_brands():
    """
    Get list of all unique brands from items
    
    Returns:
        dict: List of brands
    """
    try:
        brands = frappe.db.sql("""
            SELECT DISTINCT brand_name
            FROM `tabItem`
            WHERE brand_name IS NOT NULL AND brand_name != ''
            ORDER BY brand_name ASC
        """, as_dict=True)
        
        # Convert to simple list of brand names
        brand_list = [brand.brand_name for brand in brands]
        
        return {
            "success": True,
            "data": brand_list
        }
    except Exception as e:
        frappe.log_error(f"Error in get_brands: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to retrieve brands: {str(e)}"
        }