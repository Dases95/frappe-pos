import frappe
from frappe import _
from frappe.utils import flt, date_diff, getdate, nowdate, add_days

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
        {"label": _("Batch"), "fieldname": "batch_no", "fieldtype": "Link", "options": "Batch", "width": 120},
        {"label": _("Warehouse"), "fieldname": "warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 120},
        {"label": _("Quantity"), "fieldname": "quantity", "fieldtype": "Float", "width": 100},
        {"label": _("Manufacturing Date"), "fieldname": "manufacturing_date", "fieldtype": "Date", "width": 120},
        {"label": _("Expiry Date"), "fieldname": "expiry_date", "fieldtype": "Date", "width": 120},
        {"label": _("Days to Expiry"), "fieldname": "days_to_expiry", "fieldtype": "Int", "width": 110},
        {"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 100},
        {"label": _("Stock Value"), "fieldname": "stock_value", "fieldtype": "Currency", "width": 120},
    ]

def get_data(filters):
    conditions = ["b.expiry_date IS NOT NULL"]
    values = {}
    
    if filters.get("item"):
        conditions.append("b.item = %(item)s")
        values["item"] = filters.get("item")
    
    if filters.get("warehouse"):
        conditions.append("sle.warehouse = %(warehouse)s")
        values["warehouse"] = filters.get("warehouse")
    
    if filters.get("status"):
        # Will filter by status after calculation
        pass
    
    where_clause = " AND ".join(conditions)
    
    # Get batches with expiry dates and their current stock
    query = f"""
        SELECT 
            b.item,
            b.name as batch_no,
            b.manufacturing_date,
            b.expiry_date,
            sle.warehouse,
            SUM(sle.actual_qty) as quantity,
            SUM(sle.actual_qty * sle.valuation_rate) as stock_value
        FROM 
            "tabBatch" b
        LEFT JOIN 
            "tabStock Ledger Entry" sle ON sle.batch_no = b.name AND sle.is_cancelled = 0
        WHERE 
            {where_clause}
        GROUP BY 
            b.item, b.name, b.manufacturing_date, b.expiry_date, sle.warehouse
        HAVING 
            SUM(sle.actual_qty) > 0
        ORDER BY 
            b.expiry_date ASC, b.item
    """
    
    batch_data = frappe.db.sql(query, values=values, as_dict=1)
    
    today = getdate(nowdate())
    result = []
    
    # Define expiry thresholds (days)
    expired_threshold = 0
    expiring_soon_threshold = filters.get("expiring_soon_days", 30)  # Default 30 days
    warning_threshold = filters.get("warning_days", 90)  # Default 90 days
    
    for row in batch_data:
        item_name = frappe.get_value("Item", row.item, "item_name") or ""
        expiry_date = row.expiry_date
        
        if not expiry_date:
            continue
        
        # Calculate days to expiry
        days_to_expiry = date_diff(expiry_date, today)
        
        # Determine status
        if days_to_expiry < expired_threshold:
            status = "Expired"
        elif days_to_expiry <= expiring_soon_threshold:
            status = "Expiring Soon"
        elif days_to_expiry <= warning_threshold:
            status = "Warning"
        else:
            status = "Good"
        
        # Filter by status if specified
        if filters.get("status") and filters.get("status") != status:
            continue
        
        # Skip "Good" status if hide_good is enabled
        if filters.get("hide_good") and status == "Good":
            continue
        
        result.append({
            "item": row.item,
            "item_name": item_name,
            "batch_no": row.batch_no,
            "warehouse": row.warehouse,
            "quantity": flt(row.quantity),
            "manufacturing_date": row.manufacturing_date,
            "expiry_date": expiry_date,
            "days_to_expiry": days_to_expiry,
            "status": status,
            "stock_value": flt(row.stock_value)
        })
    
    return result

def get_chart(data):
    if not data:
        return None
    
    # Count items by status
    status_counts = {}
    status_values = {}
    
    for d in data:
        status = d.get("status", "Good")
        qty = d.get("quantity", 0)
        
        if status not in status_counts:
            status_counts[status] = 0
            status_values[status] = 0
        
        status_counts[status] += 1
        status_values[status] += qty
    
    # Sort by priority (Expired, Expiring Soon, Warning, Good)
    status_order = ["Expired", "Expiring Soon", "Warning", "Good"]
    labels = [s for s in status_order if s in status_counts]
    counts = [status_counts[s] for s in labels]
    
    # Color mapping
    color_map = {
        "Expired": "#dc3545",
        "Expiring Soon": "#fd7e14",
        "Warning": "#ffc107",
        "Good": "#28a745"
    }
    colors = [color_map.get(label, "#6c757d") for label in labels]
    
    return {
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "name": _("Batches"),
                    "values": counts
                }
            ]
        },
        "type": "pie",
        "colors": colors
    }

