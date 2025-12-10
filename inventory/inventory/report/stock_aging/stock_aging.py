import frappe
from frappe import _
from frappe.utils import flt, date_diff, getdate, nowdate

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
        {"label": _("Batch"), "fieldname": "batch_no", "fieldtype": "Link", "options": "Batch", "width": 100},
        {"label": _("Available Qty"), "fieldname": "balance_qty", "fieldtype": "Float", "width": 100},
        {"label": _("First Receipt Date"), "fieldname": "first_receipt_date", "fieldtype": "Date", "width": 120},
        {"label": _("Age (Days)"), "fieldname": "age_days", "fieldtype": "Int", "width": 90},
        {"label": _("0-30 Days"), "fieldname": "range_0_30", "fieldtype": "Float", "width": 90},
        {"label": _("31-60 Days"), "fieldname": "range_31_60", "fieldtype": "Float", "width": 90},
        {"label": _("61-90 Days"), "fieldname": "range_61_90", "fieldtype": "Float", "width": 90},
        {"label": _("90+ Days"), "fieldname": "range_90_plus", "fieldtype": "Float", "width": 90},
        {"label": _("Stock Value"), "fieldname": "stock_value", "fieldtype": "Currency", "width": 120},
    ]

def get_data(filters):
    conditions = ["is_cancelled = 0"]
    values = {}
    
    if filters.get("item"):
        conditions.append("item = %(item)s")
        values["item"] = filters.get("item")
    
    if filters.get("warehouse"):
        conditions.append("warehouse = %(warehouse)s")
        values["warehouse"] = filters.get("warehouse")
    
    where_clause = " AND ".join(conditions)
    
    # Get current stock balance grouped by item, warehouse, batch
    query = f"""
        SELECT 
            item,
            warehouse,
            batch_no,
            SUM(actual_qty) as balance_qty,
            MIN(CASE WHEN actual_qty > 0 THEN posting_date END) as first_receipt_date,
            SUM(actual_qty * valuation_rate) as stock_value
        FROM 
            "tabStock Ledger Entry"
        WHERE 
            {where_clause}
        GROUP BY 
            item, warehouse, batch_no
        HAVING 
            SUM(actual_qty) > 0
        ORDER BY 
            item, warehouse, batch_no
    """
    
    stock_data = frappe.db.sql(query, values=values, as_dict=1)
    
    today = getdate(nowdate())
    result = []
    
    for row in stock_data:
        item_name = frappe.get_value("Item", row.item, "item_name") or ""
        
        # Calculate age
        first_receipt_date = row.first_receipt_date
        age_days = 0
        if first_receipt_date:
            age_days = date_diff(today, first_receipt_date)
        
        # Categorize by age range
        balance_qty = flt(row.balance_qty)
        range_0_30 = 0
        range_31_60 = 0
        range_61_90 = 0
        range_90_plus = 0
        
        if age_days <= 30:
            range_0_30 = balance_qty
        elif age_days <= 60:
            range_31_60 = balance_qty
        elif age_days <= 90:
            range_61_90 = balance_qty
        else:
            range_90_plus = balance_qty
        
        result.append({
            "item": row.item,
            "item_name": item_name,
            "warehouse": row.warehouse,
            "batch_no": row.batch_no,
            "balance_qty": balance_qty,
            "first_receipt_date": first_receipt_date,
            "age_days": age_days,
            "range_0_30": range_0_30,
            "range_31_60": range_31_60,
            "range_61_90": range_61_90,
            "range_90_plus": range_90_plus,
            "stock_value": flt(row.stock_value)
        })
    
    return result

def get_chart(data):
    if not data:
        return None
    
    # Summarize by age range
    range_0_30 = sum(d.get("range_0_30", 0) for d in data)
    range_31_60 = sum(d.get("range_31_60", 0) for d in data)
    range_61_90 = sum(d.get("range_61_90", 0) for d in data)
    range_90_plus = sum(d.get("range_90_plus", 0) for d in data)
    
    return {
        "data": {
            "labels": ["0-30 Days", "31-60 Days", "61-90 Days", "90+ Days"],
            "datasets": [
                {
                    "name": _("Stock Quantity"),
                    "values": [range_0_30, range_31_60, range_61_90, range_90_plus]
                }
            ]
        },
        "type": "pie",
        "colors": ["#28a745", "#ffc107", "#fd7e14", "#dc3545"]
    }
