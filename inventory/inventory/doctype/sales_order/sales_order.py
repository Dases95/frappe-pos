import frappe
from frappe.model.document import Document
from frappe.utils import getdate, now_datetime

class SalesOrder(Document):
    def validate(self):
        # Validate customer
        if not self.customer:
            frappe.throw("Customer is required")
        
        # Validate items
        if not self.items:
            frappe.throw("At least one item is required")
        
        # Auto-fetch rates for items if not set
        for item in self.items:
            if not item.rate and item.item:
                price_info = get_item_price(item.item, self.customer, self.order_date)
                if price_info and price_info.get('rate'):
                    item.rate = price_info.get('rate')
        
        # Calculate total amount
        total_amount = 0
        for item in self.items:
            # Ensure amount is calculated
            if not item.amount:
                item.amount = item.quantity * item.rate
            total_amount += item.amount
        
        self.total_amount = total_amount
        
        # Validate dates
        if self.expected_delivery_date and getdate(self.order_date) > getdate(self.expected_delivery_date):
            frappe.throw("Expected Delivery Date cannot be before Order Date")
        
        # Check stock availability
        self.check_stock_availability()
    
    def check_stock_availability(self):
        """
        Check if stock is available for all items
        """
        for item in self.items:
            # Get available stock from all warehouses
            available_stock = frappe.db.sql("""
                SELECT SUM(actual_qty) 
                FROM `tabStock Ledger Entry` 
                WHERE item = %s AND is_cancelled = 0
            """, item.item)[0][0] or 0
            
            if available_stock < item.quantity:
                frappe.msgprint(f"Insufficient stock for item {item.item_name} ({item.item}). Available: {available_stock}, Required: {item.quantity}")
    
    def on_submit(self):
        # Update status
        self.status = "Ordered"
    
    def on_cancel(self):
        # Update status
        self.status = "Cancelled"
    
    def update_status(self, status):
        """
        Update the status of the Sales Order
        """
        if status not in ["Draft", "Ordered", "Partially Delivered", "Completed", "Cancelled"]:
            frappe.throw("Invalid Status")
        
        self.status = status
        self.save()
        
    def create_delivery_note(self):
        """
        Create a Delivery Note from the Sales Order
        """
        # Create Delivery Note
        dn = frappe.new_doc("Delivery Note")
        dn.customer = self.customer
        dn.delivery_date = now_datetime().date()
        dn.sales_order = self.name
        
        # Add items from Sales Order
        for item in self.items:
            dn.append("items", {
                "item": item.item,
                "quantity": item.quantity,
                "rate": item.rate,
                "amount": item.amount
            })
        
        dn.total_amount = self.total_amount
        
        return dn


@frappe.whitelist()
def search_item_by_barcode(search_value):
    """
    Search for an item by barcode, item code, or item name
    Returns the first matching item
    """
    if not search_value:
        return {"error": "Please enter a barcode, item code, or item name"}
    
    search_value = search_value.strip()
    
    # First, try exact barcode match
    barcode_item = frappe.db.sql("""
        SELECT ib.parent as item_code, i.item_name
        FROM `tabItem Barcode` ib
        INNER JOIN `tabItem` i ON i.item_code = ib.parent
        WHERE ib.barcode = %s AND i.disabled = 0
        LIMIT 1
    """, (search_value,), as_dict=True)
    
    if barcode_item:
        return {
            "item_code": barcode_item[0].item_code,
            "item_name": barcode_item[0].item_name
        }
    
    # Try exact item code match
    item_code_match = frappe.db.sql("""
        SELECT item_code, item_name
        FROM `tabItem`
        WHERE item_code = %s AND disabled = 0
        LIMIT 1
    """, (search_value,), as_dict=True)
    
    if item_code_match:
        return {
            "item_code": item_code_match[0].item_code,
            "item_name": item_code_match[0].item_name
        }
    
    # Try partial match on item code or item name
    partial_match = frappe.db.sql("""
        SELECT item_code, item_name
        FROM `tabItem`
        WHERE (item_code LIKE %s OR item_name LIKE %s) AND disabled = 0
        ORDER BY 
            CASE 
                WHEN item_code = %s THEN 1
                WHEN item_code LIKE %s THEN 2
                WHEN item_name LIKE %s THEN 3
                ELSE 4
            END
        LIMIT 1
    """, (f"%{search_value}%", f"%{search_value}%", search_value, f"{search_value}%", f"{search_value}%"), as_dict=True)
    
    if partial_match:
        return {
            "item_code": partial_match[0].item_code,
            "item_name": partial_match[0].item_name
        }
    
    # No match found
    return {"error": f"No item found matching '<b>{search_value}</b>'.<br>Please check the barcode, item code, or item name."}


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def item_query(doctype, txt, searchfield, start, page_len, filters):
    """
    Custom query to search items by:
    - Item Code
    - Item Name
    - Barcode
    """
    conditions = []
    values = []
    
    # Add disabled filter
    if filters and filters.get("disabled") is not None:
        conditions.append("disabled = %s")
        values.append(filters.get("disabled"))
    
    # Search in item_code and item_name
    if txt:
        # First, check if txt matches a barcode
        barcode_items = frappe.db.sql("""
            SELECT parent
            FROM `tabItem Barcode`
            WHERE barcode = %s
        """, (txt,), as_dict=True)
        
        if barcode_items:
            # If barcode found, return those items
            item_codes = [item.parent for item in barcode_items]
            placeholders = ', '.join(['%s'] * len(item_codes))
            where_clause = f"item_code IN ({placeholders})"
            if conditions:
                where_clause += " AND " + " AND ".join(conditions)
            
            return frappe.db.sql(f"""
                SELECT item_code, item_name
                FROM `tabItem`
                WHERE {where_clause}
                ORDER BY item_name
                LIMIT %s OFFSET %s
            """, tuple(item_codes + values + [page_len, start]))
        
        # If no barcode match, search by item_code and item_name
        search_condition = "(item_code LIKE %s OR item_name LIKE %s)"
        if conditions:
            search_condition = " AND ".join(conditions) + " AND " + search_condition
        
        search_txt = f"%{txt}%"
        
        return frappe.db.sql(f"""
            SELECT item_code, item_name
            FROM `tabItem`
            WHERE {search_condition}
            ORDER BY 
                CASE 
                    WHEN item_code LIKE %s THEN 1
                    WHEN item_name LIKE %s THEN 2
                    ELSE 3
                END,
                item_name
            LIMIT %s OFFSET %s
        """, tuple(values + [search_txt, search_txt, f"{txt}%", f"{txt}%", page_len, start]))
    
    # No search text, return all items matching filters
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    return frappe.db.sql(f"""
        SELECT item_code, item_name
        FROM `tabItem`
        WHERE {where_clause}
        ORDER BY item_name
        LIMIT %s OFFSET %s
    """, tuple(values + [page_len, start]))


@frappe.whitelist()
def get_item_price(item_code, customer, transaction_date=None):
    """
    Get item price for sales based on customer and date
    Priority:
    1. Customer-specific price within validity dates
    2. Default price (is_default_price=1) within validity dates
    3. Return error if no price found
    """
    if not transaction_date:
        transaction_date = getdate()
    else:
        transaction_date = getdate(transaction_date)
    
    # First, try to get customer-specific price
    customer_price = frappe.db.sql("""
        SELECT price_list_rate, valid_from, valid_upto
        FROM `tabItem Price`
        WHERE item_code = %s
            AND customer = %s
            AND selling = 1
            AND enabled = 1
            AND (valid_from IS NULL OR valid_from <= %s)
            AND (valid_upto IS NULL OR valid_upto >= %s)
        ORDER BY valid_from DESC
        LIMIT 1
    """, (item_code, customer, transaction_date, transaction_date), as_dict=True)
    
    if customer_price:
        return {
            'rate': customer_price[0].price_list_rate,
            'price_type': 'customer_specific',
            'valid_from': customer_price[0].valid_from,
            'valid_upto': customer_price[0].valid_upto
        }
    
    # If no customer-specific price, try to get default price
    default_price = frappe.db.sql("""
        SELECT price_list_rate, valid_from, valid_upto
        FROM `tabItem Price`
        WHERE item_code = %s
            AND selling = 1
            AND enabled = 1
            AND is_default_price = 1
            AND (customer IS NULL OR customer = '')
            AND (valid_from IS NULL OR valid_from <= %s)
            AND (valid_upto IS NULL OR valid_upto >= %s)
        ORDER BY valid_from DESC
        LIMIT 1
    """, (item_code, transaction_date, transaction_date), as_dict=True)
    
    if default_price:
        return {
            'rate': default_price[0].price_list_rate,
            'price_type': 'default',
            'valid_from': default_price[0].valid_from,
            'valid_upto': default_price[0].valid_upto
        }
    
    # No price found
    item_name = frappe.db.get_value("Item", item_code, "item_name")
    return {
        'rate': None,
        'error': f"No sales price found for item <b>{item_name} ({item_code})</b>.<br>"
                 f"Please create an Item Price with:<br>"
                 f"- Selling enabled<br>"
                 f"- Valid date range including {transaction_date}<br>"
                 f"- Either customer-specific or marked as default price"
    } 