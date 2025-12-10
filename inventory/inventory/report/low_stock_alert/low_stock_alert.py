import frappe
from frappe import _
from frappe.utils import flt, add_days, nowdate

def execute(filters=None):
    if not filters:
        filters = {}
    
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart(data)
    
    return columns, data, None, chart

def get_columns():
    return [
        {"label": _("Item"), "fieldname": "item", "fieldtype": "Link", "options": "Item", "width": 120},
        {"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 150},
        {"label": _("Warehouse"), "fieldname": "warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 120},
        {"label": _("Current Stock"), "fieldname": "current_stock", "fieldtype": "Float", "width": 110},
        {"label": _("Reorder Level"), "fieldname": "reorder_level", "fieldtype": "Float", "width": 110},
        {"label": _("Min Stock Level"), "fieldname": "min_stock_level", "fieldtype": "Float", "width": 110},
        {"label": _("Shortage"), "fieldname": "shortage", "fieldtype": "Float", "width": 100},
        {"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 100},
        {"label": _("Last Purchase"), "fieldname": "last_purchase_date", "fieldtype": "Date", "width": 110},
        {"label": _("Avg Daily Sales"), "fieldname": "avg_daily_sales", "fieldtype": "Float", "width": 110},
        {"label": _("Days of Stock"), "fieldname": "days_of_stock", "fieldtype": "Float", "width": 100},
    ]

def get_data(filters):
    conditions = ["i.disabled = 0"]
    values = {}
    
    if filters.get("item"):
        conditions.append("i.name = %(item)s")
        values["item"] = filters.get("item")
    
    # Only show items with reorder level or minimum stock level set, or filter for all items
    if not filters.get("show_all"):
        conditions.append("(i.reorder_level > 0 OR i.minimum_stock_level > 0)")
    
    where_clause = " AND ".join(conditions)
    
    # Get items with stock levels
    query = f"""
        SELECT 
            i.name as item,
            i.item_name,
            i.reorder_level,
            i.minimum_stock_level,
            i.default_warehouse
        FROM 
            "tabItem" i
        WHERE 
            {where_clause}
        ORDER BY 
            i.item_name
    """
    
    items = frappe.db.sql(query, values=values, as_dict=1)
    
    result = []
    warehouse_filter = filters.get("warehouse")
    
    for row in items:
        # Get current stock for this item
        stock_conditions = ["item = %(item)s", "is_cancelled = 0"]
        stock_values = {"item": row.item}
        
        if warehouse_filter:
            stock_conditions.append("warehouse = %(warehouse)s")
            stock_values["warehouse"] = warehouse_filter
        
        stock_where = " AND ".join(stock_conditions)
        
        stock_query = f"""
            SELECT 
                warehouse,
                SUM(actual_qty) as current_stock
            FROM 
                "tabStock Ledger Entry"
            WHERE 
                {stock_where}
            GROUP BY 
                warehouse
        """
        
        stock_data = frappe.db.sql(stock_query, stock_values, as_dict=1)
        
        # If no stock data, create a single row with 0 stock
        if not stock_data:
            stock_data = [{"warehouse": row.default_warehouse or warehouse_filter or "N/A", "current_stock": 0}]
        
        for stock_row in stock_data:
            current_stock = flt(stock_row.current_stock)
            reorder_level = flt(row.reorder_level)
            min_stock_level = flt(row.minimum_stock_level)
            
            # Use reorder_level if set, otherwise use minimum_stock_level
            threshold = reorder_level if reorder_level > 0 else min_stock_level
            
            # Calculate shortage
            shortage = threshold - current_stock if current_stock < threshold else 0
            
            # Determine status
            if current_stock <= 0:
                status = "Out of Stock"
            elif threshold > 0 and current_stock < threshold:
                status = "Low Stock"
            elif threshold > 0 and current_stock < threshold * 1.5:
                status = "Warning"
            else:
                status = "OK"
            
            # Skip OK status if not showing all
            if not filters.get("show_all") and status == "OK":
                continue
            
            # Get last purchase date
            last_purchase = frappe.db.sql("""
                SELECT MAX(posting_date) as last_date
                FROM "tabStock Ledger Entry"
                WHERE item = %s AND voucher_type = 'Purchase Receipt' AND is_cancelled = 0
            """, row.item, as_dict=1)
            
            last_purchase_date = last_purchase[0].last_date if last_purchase and last_purchase[0].last_date else None
            
            # Calculate average daily sales (last 30 days)
            thirty_days_ago = add_days(nowdate(), -30)
            avg_sales = frappe.db.sql("""
                SELECT ABS(SUM(actual_qty)) / 30 as avg_daily
                FROM "tabStock Ledger Entry"
                WHERE item = %s 
                AND voucher_type = 'Delivery Note' 
                AND is_cancelled = 0
                AND posting_date >= %s
            """, (row.item, thirty_days_ago), as_dict=1)
            
            avg_daily_sales = flt(avg_sales[0].avg_daily) if avg_sales and avg_sales[0].avg_daily else 0
            
            # Calculate days of stock remaining
            days_of_stock = (current_stock / avg_daily_sales) if avg_daily_sales > 0 else 999
            
            result.append({
                "item": row.item,
                "item_name": row.item_name,
                "warehouse": stock_row.warehouse,
                "current_stock": current_stock,
                "reorder_level": reorder_level,
                "min_stock_level": min_stock_level,
                "shortage": shortage,
                "status": status,
                "last_purchase_date": last_purchase_date,
                "avg_daily_sales": avg_daily_sales,
                "days_of_stock": days_of_stock if days_of_stock < 999 else None
            })
    
    # Sort by status priority and shortage
    status_priority = {"Out of Stock": 0, "Low Stock": 1, "Warning": 2, "OK": 3}
    result.sort(key=lambda x: (status_priority.get(x["status"], 4), -x["shortage"]))
    
    return result

def get_chart(data):
    if not data:
        return None
    
    # Count items by status
    status_counts = {}
    for d in data:
        status = d.get("status", "OK")
        status_counts[status] = status_counts.get(status, 0) + 1
    
    labels = list(status_counts.keys())
    values = list(status_counts.values())
    
    # Color mapping
    colors = []
    for label in labels:
        if label == "Out of Stock":
            colors.append("#dc3545")
        elif label == "Low Stock":
            colors.append("#fd7e14")
        elif label == "Warning":
            colors.append("#ffc107")
        else:
            colors.append("#28a745")
    
    return {
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "name": _("Items"),
                    "values": values
                }
            ]
        },
        "type": "pie",
        "colors": colors
    }
