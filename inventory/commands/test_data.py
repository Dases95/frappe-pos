import os
import click
import frappe
import random
from datetime import datetime, timedelta
from frappe.commands import get_site, pass_context
from frappe.utils import today, add_days, flt

# Algerian business data for realistic test generation
ALGERIAN_COMPANIES = [
    "شركة الجزائر للتجارة", "مؤسسة الأطلس التجارية", "شركة النور للاستيراد والتصدير",
    "مؤسسة البركة للتجارة العامة", "شركة الهضاب للمواد الغذائية", "مؤسسة الساحل التجارية",
    "شركة الصحراء للتوزيع", "مؤسسة القبائل للتجارة", "شركة الأوراس التجارية",
    "مؤسسة المتوسط للاستيراد", "شركة الزيبان للتجارة", "مؤسسة الونشريس التجارية"
]

ALGERIAN_FIRST_NAMES = [
    "محمد", "أحمد", "علي", "حسن", "عبد الله", "عمر", "يوسف", "إبراهيم", "خالد", "عبد الرحمن",
    "فاطمة", "عائشة", "خديجة", "زينب", "مريم", "سارة", "أمينة", "نور", "هدى", "ليلى"
]

ALGERIAN_LAST_NAMES = [
    "بن علي", "بن محمد", "بوعلام", "بلعيد", "حمداني", "زروقي", "مرابط", "قاسمي",
    "بوزيد", "عثماني", "جعفري", "سليماني", "رحماني", "بوضياف", "معمري"
]

ALGERIAN_PRODUCTS = [
    # Food items
    {"name": "كسكس", "category": "مواد غذائية", "unit": "كيلوغرام", "price_range": (200, 400)},
    {"name": "زيت الزيتون", "category": "مواد غذائية", "unit": "لتر", "price_range": (800, 1500)},
    {"name": "تمر دقلة نور", "category": "مواد غذائية", "unit": "كيلوغرام", "price_range": (1200, 2000)},
    {"name": "قمح صلب", "category": "مواد غذائية", "unit": "كيلوغرام", "price_range": (80, 120)},
    {"name": "شعير", "category": "مواد غذائية", "unit": "كيلوغرام", "price_range": (60, 100)},
    {"name": "عدس", "category": "مواد غذائية", "unit": "كيلوغرام", "price_range": (150, 250)},
    {"name": "حمص", "category": "مواد غذائية", "unit": "كيلوغرام", "price_range": (180, 280)},
    {"name": "سكر أبيض", "category": "مواد غذائية", "unit": "كيلوغرام", "price_range": (100, 150)},
    {"name": "شاي أخضر", "category": "مشروبات", "unit": "علبة", "price_range": (300, 500)},
    {"name": "قهوة عربية", "category": "مشروبات", "unit": "كيلوغرام", "price_range": (2000, 3500)},
    
    # Textiles
    {"name": "قماش قطني", "category": "منسوجات", "unit": "متر", "price_range": (500, 800)},
    {"name": "صوف طبيعي", "category": "منسوجات", "unit": "كيلوغرام", "price_range": (3000, 5000)},
    {"name": "حرير", "category": "منسوجات", "unit": "متر", "price_range": (2000, 4000)},
    
    # Electronics
    {"name": "هاتف ذكي", "category": "إلكترونيات", "unit": "قطعة", "price_range": (25000, 80000)},
    {"name": "حاسوب محمول", "category": "إلكترونيات", "unit": "قطعة", "price_range": (60000, 150000)},
    {"name": "تلفزيون", "category": "إلكترونيات", "unit": "قطعة", "price_range": (40000, 120000)},
    
    # Construction materials
    {"name": "إسمنت", "category": "مواد البناء", "unit": "كيس", "price_range": (800, 1200)},
    {"name": "حديد التسليح", "category": "مواد البناء", "unit": "طن", "price_range": (80000, 120000)},
    {"name": "رمل", "category": "مواد البناء", "unit": "متر مكعب", "price_range": (2000, 3000)},
    {"name": "حصى", "category": "مواد البناء", "unit": "متر مكعب", "price_range": (2500, 3500)},
]

def create_test_customers(count=50):
    """Create test customers with Algerian names and addresses"""
    print(f"Creating {count} test customers...")
    
    # Get all wilayas for random assignment
    wilayas = frappe.get_all("Wilaya", fields=["name", "wilaya_name"])
    if not wilayas:
        print("Warning: No Wilayas found. Please install geography fixtures first.")
        return
    
    customers_created = 0
    for i in range(count):
        try:
            first_name = random.choice(ALGERIAN_FIRST_NAMES)
            last_name = random.choice(ALGERIAN_LAST_NAMES)
            customer_name = f"{first_name} {last_name}"
            
            # Some customers are companies
            if random.random() < 0.3:  # 30% companies
                customer_name = random.choice(ALGERIAN_COMPANIES)
                customer_type = "Company"
            else:
                customer_type = "Individual"
            
            wilaya = random.choice(wilayas)
            
            customer = frappe.get_doc({
                "doctype": "Customer",
                "customer_name": customer_name,
                "customer_type": customer_type,
                "territory": wilaya["wilaya_name"],
                "customer_group": "Commercial" if customer_type == "Company" else "Individual",
                "mobile_no": f"0{random.randint(5,7)}{random.randint(10000000, 99999999)}",
                "email_id": f"{frappe.scrub(customer_name)}@example.dz" if random.random() < 0.7 else None,
                "address_line1": f"حي {random.choice(['النصر', 'السلام', 'الشهداء', 'الإخوة', 'الوحدة'])}",
                "city": wilaya["wilaya_name"],
                "state": wilaya["wilaya_name"],
                "country": "Algeria"
            })
            
            customer.insert(ignore_permissions=True)
            customers_created += 1
            
        except Exception as e:
            print(f"Error creating customer {i+1}: {e}")
            continue
    
    print(f"Successfully created {customers_created} customers")

def create_test_suppliers(count=20):
    """Create test suppliers"""
    print(f"Creating {count} test suppliers...")
    
    wilayas = frappe.get_all("Wilaya", fields=["name", "wilaya_name"])
    if not wilayas:
        print("Warning: No Wilayas found. Please install geography fixtures first.")
        return
    
    suppliers_created = 0
    for i in range(count):
        try:
            supplier_name = random.choice(ALGERIAN_COMPANIES)
            wilaya = random.choice(wilayas)
            
            supplier = frappe.get_doc({
                "doctype": "Supplier",
                "supplier_name": supplier_name,
                "supplier_group": "Local",
                "country": "Algeria",
                "state": wilaya["wilaya_name"],
                "city": wilaya["wilaya_name"],
                "mobile_no": f"0{random.randint(2,3)}{random.randint(10000000, 99999999)}",
                "email_id": f"{frappe.scrub(supplier_name)}@supplier.dz"
            })
            
            supplier.insert(ignore_permissions=True)
            suppliers_created += 1
            
        except Exception as e:
            print(f"Error creating supplier {i+1}: {e}")
            continue
    
    print(f"Successfully created {suppliers_created} suppliers")

def create_test_items(count=None):
    """Create test items based on Algerian products"""
    if count is None:
        count = len(ALGERIAN_PRODUCTS)
    
    print(f"Creating {count} test items...")
    
    # Create item groups first
    categories = list(set([product["category"] for product in ALGERIAN_PRODUCTS]))
    for category in categories:
        if not frappe.db.exists("Item Group", category):
            item_group = frappe.get_doc({
                "doctype": "Item Group",
                "item_group_name": category,
                "parent_item_group": "All Item Groups"
            })
            item_group.insert(ignore_permissions=True)
    
    items_created = 0
    products_to_create = ALGERIAN_PRODUCTS[:count] if count < len(ALGERIAN_PRODUCTS) else ALGERIAN_PRODUCTS
    
    for product in products_to_create:
        try:
            item_code = frappe.scrub(product["name"]).upper()
            
            if frappe.db.exists("Item", item_code):
                continue
            
            item = frappe.get_doc({
                "doctype": "Item",
                "item_code": item_code,
                "item_name": product["name"],
                "item_group": product["category"],
                "unit_of_measurement": product["unit"],
                "is_stock_item": 1,
                "include_item_in_manufacturing": 1,
                "standard_rate": random.randint(*product["price_range"]),
                "opening_stock": random.randint(10, 1000),
                "valuation_rate": random.randint(*product["price_range"]),
                "description": f"منتج جزائري عالي الجودة - {product['name']}"
            })
            
            item.insert(ignore_permissions=True)
            items_created += 1
            
        except Exception as e:
            print(f"Error creating item {product['name']}: {e}")
            continue
    
    print(f"Successfully created {items_created} items")

def create_test_warehouses():
    """Create test warehouses for major Algerian cities"""
    print("Creating test warehouses...")
    
    major_cities = [
        "الجزائر العاصمة", "وهران", "قسنطينة", "عنابة", "باتنة", "سطيف", "سيدي بلعباس", "بسكرة"
    ]
    
    warehouses_created = 0
    for city in major_cities:
        try:
            warehouse_name = f"مستودع {city}"
            
            if frappe.db.exists("Warehouse", warehouse_name):
                continue
            
            warehouse = frappe.get_doc({
                "doctype": "Warehouse",
                "warehouse_name": warehouse_name,
                "warehouse_type": "Stock",
                "is_group": 0,
                "parent_warehouse": None
            })
            
            warehouse.insert(ignore_permissions=True)
            warehouses_created += 1
            
        except Exception as e:
            print(f"Error creating warehouse for {city}: {e}")
            continue
    
    print(f"Successfully created {warehouses_created} warehouses")

def create_test_transactions(count=100):
    """Create test sales orders and purchase orders"""
    print(f"Creating {count} test transactions...")
    
    customers = frappe.get_all("Customer", fields=["name"])
    suppliers = frappe.get_all("Supplier", fields=["name"])
    items = frappe.get_all("Item", fields=["name", "standard_rate"])
    
    if not customers or not suppliers or not items:
        print("Warning: Need customers, suppliers, and items to create transactions")
        return
    
    transactions_created = 0
    
    # Create sales orders
    for i in range(count // 2):
        try:
            customer = random.choice(customers)
            transaction_date = add_days(today(), random.randint(-90, 0))
            
            sales_order = frappe.get_doc({
                "doctype": "Sales Order",
                "customer": customer["name"],
                "transaction_date": transaction_date,
                "delivery_date": add_days(transaction_date, random.randint(1, 30)),
                "items": []
            })
            
            # Add random items
            num_items = random.randint(1, 5)
            for _ in range(num_items):
                item = random.choice(items)
                qty = random.randint(1, 50)
                rate = item["standard_rate"] * random.uniform(0.9, 1.1)  # ±10% variation
                
                sales_order.append("items", {
                    "item": item["name"],
                    "quantity": qty,
                    "rate": flt(rate, 2),
                    "amount": flt(qty * rate, 2)
                })
            
            sales_order.insert(ignore_permissions=True)
            transactions_created += 1
            
        except Exception as e:
            print(f"Error creating sales order {i+1}: {e}")
            continue
    
    # Create purchase orders
    for i in range(count // 2):
        try:
            supplier = random.choice(suppliers)
            transaction_date = add_days(today(), random.randint(-90, 0))
            
            purchase_order = frappe.get_doc({
                "doctype": "Purchase Order",
                "supplier": supplier["name"],
                "transaction_date": transaction_date,
                "schedule_date": add_days(transaction_date, random.randint(1, 30)),
                "items": []
            })
            
            # Add random items
            num_items = random.randint(1, 5)
            for _ in range(num_items):
                item = random.choice(items)
                qty = random.randint(10, 200)
                rate = item["standard_rate"] * random.uniform(0.8, 0.95)  # Purchase at lower rate
                
                purchase_order.append("items", {
                    "item": item["name"],
                    "qty": qty,
                    "rate": flt(rate, 2),
                    "amount": flt(qty * rate, 2)
                })
            
            purchase_order.insert(ignore_permissions=True)
            transactions_created += 1
            
        except Exception as e:
            print(f"Error creating purchase order {i+1}: {e}")
            continue
    
    print(f"Successfully created {transactions_created} transactions")

@click.command('create-algeria-test-data')
@click.option('--site', help='site name')
@click.option('--customers', default=50, help='Number of customers to create')
@click.option('--suppliers', default=20, help='Number of suppliers to create')
@click.option('--items', default=None, help='Number of items to create (default: all predefined items)')
@click.option('--transactions', default=100, help='Number of transactions to create')
@pass_context
def create_algeria_test_data_command(context, site=None, customers=50, suppliers=20, items=None, transactions=100):
    """Create comprehensive test data for the Algerian market
    
    This command creates realistic test data including:
    - Customers with Algerian names and addresses
    - Suppliers from major Algerian cities
    - Products typical to the Algerian market
    - Warehouses in major cities
    - Sample sales and purchase transactions
    """
    site = get_site(context, site=site)
    with frappe.init_site(site):
        frappe.connect()
        print(f"Creating Algeria test data for site: {site}")
        print("=" * 50)
        
        try:
            # Create basic master data
            create_test_warehouses()
            create_test_items(items)
            create_test_customers(customers)
            create_test_suppliers(suppliers)
            
            # Create transactions
            create_test_transactions(transactions)
            
            frappe.db.commit()
            print("=" * 50)
            print("✅ Algeria test data creation completed successfully!")
            print(f"Created:")
            print(f"  - {customers} customers")
            print(f"  - {suppliers} suppliers")
            print(f"  - {len(ALGERIAN_PRODUCTS) if items is None else items} items")
            print(f"  - 8 warehouses")
            print(f"  - {transactions} transactions")
            
        except Exception as e:
            frappe.db.rollback()
            print(f"❌ Error creating test data: {e}")
            raise

@click.command('clear-test-data')
@click.option('--site', help='site name')
@click.option('--confirm', is_flag=True, help='Confirm deletion without prompt')
@pass_context
def clear_test_data_command(context, site=None, confirm=False):
    """Clear all test data (use with caution!)"""
    if not confirm:
        if not click.confirm('This will delete ALL customers, suppliers, items, and transactions. Continue?'):
            return
    
    site = get_site(context, site=site)
    with frappe.init_site(site):
        frappe.connect()
        print(f"Clearing test data for site: {site}")
        
        try:
            # Delete in reverse dependency order
            doctypes_to_clear = [
                "Sales Order", "Purchase Order", "Delivery Note", "Purchase Receipt",
                "Stock Entry", "Stock Ledger Entry", "Item Price",
                "Item", "Customer", "Supplier", "Warehouse", "Item Group"
            ]
            
            for doctype in doctypes_to_clear:
                count = frappe.db.count(doctype)
                if count > 0:
                    frappe.db.sql(f"DELETE FROM `tab{doctype}`")
                    print(f"Deleted {count} {doctype} records")
            
            frappe.db.commit()
            print("✅ Test data cleared successfully!")
            
        except Exception as e:
            frappe.db.rollback()
            print(f"❌ Error clearing test data: {e}")
            raise

commands = [
    create_algeria_test_data_command,
    clear_test_data_command
]