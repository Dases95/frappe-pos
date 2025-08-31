import frappe
from frappe.model.document import Document

class ItemPrice(Document):
    def validate(self):
        # Validate that price_list_rate is positive
        if self.price_list_rate <= 0:
            frappe.throw("Price List Rate must be greater than zero")
            
        # Validate date range
        if self.valid_from and self.valid_upto and self.valid_from > self.valid_upto:
            frappe.throw("Valid From date cannot be after Valid Upto date")
        
        # Validate that either buying or selling is checked
        if not self.buying and not self.selling:
            frappe.throw("At least one of Buying or Selling must be checked")
        
        # Validate default price is used correctly
        if self.is_default_price:
            # If default price, supplier should not be set
            if self.supplier:
                frappe.throw("Supplier cannot be set for Default Price. Default prices are used when no supplier-specific price is found.")

            # If default price, validate we have only one default per item per type (buying or selling)
            self.validate_default_price()
        
        # Validate that customer is set only for selling prices
        if self.customer and not self.selling:
            frappe.throw("Customer can only be set for selling prices")
        
        # Validate that supplier is set only for buying prices
        if self.supplier and not self.buying:
            frappe.throw("Supplier can only be set for buying prices")
        
        # Check for duplicate price entry for the same item
        self.validate_duplicate_item_price()
        
    def validate_default_price(self):
        """Validate that there is only one default price per item per type (buying or selling)"""
        # Check for existing default prices for this item
        existing_default = frappe.db.get_all(
            "Item Price",
            filters={
                "item_code": self.item_code,
                "is_default_price": 1,
                "buying": 1 if self.buying else 0,
                "selling": 1 if self.selling else 0,
                "name": ["!=", self.name or "New Item Price"]
            },
            limit=1
        )
        
        if existing_default:
            price_type = "buying" if self.buying else "selling"
            frappe.throw(f"Item {self.item_code} already has a default {price_type} price. Only one default price per type is allowed per item.")
        
    def validate_duplicate_item_price(self):
        """Validate that there are no active duplicate prices for the same item"""
        conditions = [
            ["item_code", "=", self.item_code],
            ["buying", "=", self.buying],
            ["selling", "=", self.selling],
            ["name", "!=", self.name or "New Item Price"]
        ]
        
        # For default prices, check for duplicates with same is_default_price
        if self.is_default_price:
            conditions.append(["is_default_price", "=", 1])
        else:
            # If customer specific, check for duplicates with same customer
            if self.customer:
                conditions.append(["customer", "=", self.customer])
            else:
                conditions.append(["ifnull(customer, '')", "=", ""])
                
            # If supplier specific, check for duplicates with same supplier
            if self.supplier:
                conditions.append(["supplier", "=", self.supplier])
            else:
                conditions.append(["ifnull(supplier, '')", "=", ""])
        
        # Add date validity to conditions
        if self.valid_from:
            conditions.append(["valid_upto", ">=", self.valid_from])
        if self.valid_upto:
            conditions.append(["valid_from", "<=", self.valid_upto])
        
        duplicate_item_prices = frappe.db.get_all("Item Price", filters=conditions)
        
        if duplicate_item_prices:
            item_name = frappe.db.get_value("Item", self.item_code, "item_name")
            price_type = "default " + ("buying" if self.buying else "selling") if self.is_default_price else ("buying" if self.buying else "selling")
            
            party_msg = ""
            if self.customer:
                party_msg = f" for customer {self.customer}"
            elif self.supplier:
                party_msg = f" for supplier {self.supplier}"
                
            frappe.throw(f"Item {self.item_code} ({item_name}) already has a {price_type} price{party_msg} " +
                        "that is effective during this period. Please review existing price entries.")
                        
    def on_update(self):
        """
        Update linked documents that previously referenced Price List
        """
        # This method can be expanded to handle updates to documents
        # that previously referenced the Price List doctype directly
        pass

@frappe.whitelist()
def get_item_prices_for_pos(item_codes=None, customer=None):
    """
    Get item prices for POS system
    Returns a dictionary with item_code as key and price as value
    """
    if not item_codes:
        return {}
    
    if isinstance(item_codes, str):
        import json
        item_codes = json.loads(item_codes)
    
    today = frappe.utils.today()
    price_map = {}
    
    for item_code in item_codes:
        price = get_item_selling_price(item_code, customer, today)
        if price:
            price_map[item_code] = price
    
    return price_map

def get_item_selling_price(item_code, customer=None, date=None):
    """
    Get the best selling price for an item
    Priority: Customer-specific > Default price
    """
    if not date:
        date = frappe.utils.today()
    
    # Use raw SQL to handle null values properly
    sql_conditions = """
        item_code = %(item_code)s 
        AND selling = 1 
        AND enabled = 1 
        AND valid_from <= %(date)s
        AND (valid_upto IS NULL OR valid_upto >= %(date)s)
    """
    
    # First try to get customer-specific price if customer is provided
    if customer:
        customer_sql = sql_conditions + " AND customer = %(customer)s"
        customer_price = frappe.db.sql("""
            SELECT price_list_rate 
            FROM `tabItem Price` 
            WHERE {}
            ORDER BY valid_from DESC 
            LIMIT 1
        """.format(customer_sql), {
            'item_code': item_code,
            'customer': customer,
            'date': date
        })
        
        if customer_price and customer_price[0][0]:
            return customer_price[0][0]
    
    # If no customer-specific price found, get default price
    default_sql = sql_conditions + " AND is_default_price = 1 AND (customer IS NULL OR customer = '')"
    default_price = frappe.db.sql("""
        SELECT price_list_rate 
        FROM `tabItem Price` 
        WHERE {}
        ORDER BY valid_from DESC 
        LIMIT 1
    """.format(default_sql), {
        'item_code': item_code,
        'date': date
    })
    
    if default_price and default_price[0][0]:
        return default_price[0][0]
    
    return 0