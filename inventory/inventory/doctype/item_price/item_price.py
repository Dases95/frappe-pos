import frappe
from frappe.model.document import Document

# Cache key prefix for item prices
PRICE_CACHE_KEY = "pos_item_prices"

def get_price_cache_key(item_code, customer=None):
    """Generate a cache key for an item price"""
    if customer:
        return f"{PRICE_CACHE_KEY}:{item_code}:{customer}"
    return f"{PRICE_CACHE_KEY}:{item_code}:default"

def invalidate_item_price_cache(item_code, customer=None):
    """Invalidate cache for a specific item"""
    # Clear specific item cache
    frappe.cache().delete_value(get_price_cache_key(item_code, customer))
    frappe.cache().delete_value(get_price_cache_key(item_code, None))
    # Clear the all-prices cache
    frappe.cache().delete_value(f"{PRICE_CACHE_KEY}:all")

def invalidate_all_price_cache():
    """Invalidate all price caches"""
    frappe.cache().delete_keys(f"{PRICE_CACHE_KEY}:*")

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
        """Invalidate price cache when price is updated"""
        invalidate_item_price_cache(self.item_code, self.customer)
    
    def after_insert(self):
        """Invalidate price cache when new price is added"""
        invalidate_item_price_cache(self.item_code, self.customer)
    
    def on_trash(self):
        """Invalidate price cache when price is deleted"""
        invalidate_item_price_cache(self.item_code, self.customer)

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
    Get the best selling price for an item with caching
    Priority: Customer-specific > Default price
    Cache duration: Until invalidated by Item Price update
    """
    if not date:
        date = frappe.utils.today()
    
    # Try to get from cache first
    cache_key = get_price_cache_key(item_code, customer)
    cached_price = frappe.cache().get_value(cache_key)
    
    if cached_price is not None:
        # Verify the cached price is still valid for today
        if cached_price.get('date') == date:
            return cached_price.get('price', 0)
    
    # Fetch from database
    price = _fetch_item_price_from_db(item_code, customer, date)
    
    # Cache the result (cache for 24 hours or until invalidated)
    frappe.cache().set_value(cache_key, {
        'price': price,
        'date': date
    }, expires_in_sec=86400)  # 24 hours
    
    return price

def _fetch_item_price_from_db(item_code, customer=None, date=None):
    """
    Fetch item price from database (internal function)
    """
    if not date:
        date = frappe.utils.today()
    
    # Use raw SQL to handle null values properly
    sql_conditions = """
        item_code = %(item_code)s 
        AND selling = 1 
        AND enabled = 1 
        AND (valid_from IS NULL OR valid_from <= %(date)s)
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
    
    # If no customer-specific price found, get default selling price
    default_sql = sql_conditions + " AND (customer IS NULL OR customer = '')"
    default_price = frappe.db.sql("""
        SELECT price_list_rate 
        FROM `tabItem Price` 
        WHERE {}
        ORDER BY is_default_price DESC, valid_from DESC 
        LIMIT 1
    """.format(default_sql), {
        'item_code': item_code,
        'date': date
    })
    
    if default_price and default_price[0][0]:
        return default_price[0][0]
    
    return 0

@frappe.whitelist()
def get_all_selling_prices_cached():
    """
    Get all selling prices at once (cached for POS)
    Returns a dictionary with item_code as key and price as value
    """
    cache_key = f"{PRICE_CACHE_KEY}:all"
    cached_prices = frappe.cache().get_value(cache_key)
    
    if cached_prices is not None:
        return cached_prices
    
    # Fetch all active selling prices from database
    today = frappe.utils.today()
    
    prices = frappe.db.sql("""
        SELECT 
            ip.item_code,
            ip.price_list_rate,
            ip.customer,
            ip.is_default_price
        FROM `tabItem Price` ip
        WHERE ip.selling = 1 
            AND ip.enabled = 1
            AND (ip.valid_from IS NULL OR ip.valid_from <= %(today)s)
            AND (ip.valid_upto IS NULL OR ip.valid_upto >= %(today)s)
        ORDER BY ip.item_code, ip.is_default_price DESC, ip.valid_from DESC
    """, {'today': today}, as_dict=True)
    
    # Build price map (prioritize default prices, one per item)
    price_map = {}
    for p in prices:
        item_code = p.item_code
        # Only set if not already set (first match wins due to ORDER BY)
        if item_code not in price_map and not p.customer:
            price_map[item_code] = p.price_list_rate
    
    # Cache for 1 hour (will be invalidated on any price update)
    frappe.cache().set_value(cache_key, price_map, expires_in_sec=3600)
    
    return price_map