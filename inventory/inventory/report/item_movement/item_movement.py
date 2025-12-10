import frappe
from frappe import _
from frappe.utils import flt

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
        {"label": _("Opening Qty"), "fieldname": "opening_qty", "fieldtype": "Float", "width": 100},
        {"label": _("Purchased Qty"), "fieldname": "purchased_qty", "fieldtype": "Float", "width": 110},
        {"label": _("Purchase Value"), "fieldname": "purchase_value", "fieldtype": "Currency", "width": 120},
        {"label": _("Sold Qty"), "fieldname": "sold_qty", "fieldtype": "Float", "width": 100},
        {"label": _("Sales Value"), "fieldname": "sales_value", "fieldtype": "Currency", "width": 120},
        {"label": _("Other In"), "fieldname": "other_in_qty", "fieldtype": "Float", "width": 90},
        {"label": _("Other Out"), "fieldname": "other_out_qty", "fieldtype": "Float", "width": 90},
        {"label": _("Closing Qty"), "fieldname": "closing_qty", "fieldtype": "Float", "width": 100},
        {"label": _("Closing Value"), "fieldname": "closing_value", "fieldtype": "Currency", "width": 120},
    ]

def get_data(filters):
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    
    conditions = ["is_cancelled = 0"]
    values = {}
    
    if filters.get("item"):
        conditions.append("item = %(item)s")
        values["item"] = filters.get("item")
    
    if filters.get("warehouse"):
        conditions.append("warehouse = %(warehouse)s")
        values["warehouse"] = filters.get("warehouse")
    
    where_clause = " AND ".join(conditions)
    
    # Get all items with stock movements
    items_query = f"""
        SELECT DISTINCT item 
        FROM "tabStock Ledger Entry"
        WHERE {where_clause}
        ORDER BY item
    """
    items = frappe.db.sql(items_query, values=values, as_dict=1)
    
    result = []
    
    for item_row in items:
        item = item_row.item
        item_name = frappe.get_value("Item", item, "item_name") or ""
        
        # Get opening balance (before from_date)
        opening_qty = 0
        if from_date:
            opening_query = f"""
                SELECT SUM(actual_qty) as qty
                FROM "tabStock Ledger Entry"
                WHERE item = %(item)s 
                AND posting_date < %(from_date)s
                AND is_cancelled = 0
                {"AND warehouse = %(warehouse)s" if filters.get("warehouse") else ""}
            """
            opening_values = {"item": item, "from_date": from_date}
            if filters.get("warehouse"):
                opening_values["warehouse"] = filters.get("warehouse")
            
            opening_result = frappe.db.sql(opening_query, opening_values, as_dict=1)
            opening_qty = flt(opening_result[0].qty) if opening_result and opening_result[0].qty else 0
        
        # Build date range condition
        date_conditions = conditions.copy()
        date_values = values.copy()
        date_values["item"] = item
        
        if from_date:
            date_conditions.append("posting_date >= %(from_date)s")
            date_values["from_date"] = from_date
        
        if to_date:
            date_conditions.append("posting_date <= %(to_date)s")
            date_values["to_date"] = to_date
        
        date_where = " AND ".join(date_conditions) + " AND item = %(item)s"
        
        # Get movements by voucher type
        movement_query = f"""
            SELECT 
                voucher_type,
                SUM(CASE WHEN actual_qty > 0 THEN actual_qty ELSE 0 END) as qty_in,
                SUM(CASE WHEN actual_qty < 0 THEN ABS(actual_qty) ELSE 0 END) as qty_out,
                SUM(CASE WHEN actual_qty > 0 THEN actual_qty * valuation_rate ELSE 0 END) as value_in,
                SUM(CASE WHEN actual_qty < 0 THEN ABS(actual_qty) * valuation_rate ELSE 0 END) as value_out
            FROM "tabStock Ledger Entry"
            WHERE {date_where}
            GROUP BY voucher_type
        """
        
        movements = frappe.db.sql(movement_query, date_values, as_dict=1)
        
        purchased_qty = 0
        purchase_value = 0
        sold_qty = 0
        sales_value = 0
        other_in_qty = 0
        other_out_qty = 0
        
        for m in movements:
            if m.voucher_type == "Purchase Receipt":
                purchased_qty += flt(m.qty_in)
                purchase_value += flt(m.value_in)
            elif m.voucher_type == "Delivery Note":
                sold_qty += flt(m.qty_out)
                sales_value += flt(m.value_out)
            else:
                other_in_qty += flt(m.qty_in)
                other_out_qty += flt(m.qty_out)
        
        # Calculate closing
        closing_qty = opening_qty + purchased_qty + other_in_qty - sold_qty - other_out_qty
        
        # Get closing value
        closing_value_query = f"""
            SELECT SUM(actual_qty * valuation_rate) as value
            FROM "tabStock Ledger Entry"
            WHERE item = %(item)s
            AND is_cancelled = 0
            {"AND posting_date <= %(to_date)s" if to_date else ""}
            {"AND warehouse = %(warehouse)s" if filters.get("warehouse") else ""}
        """
        closing_values = {"item": item}
        if to_date:
            closing_values["to_date"] = to_date
        if filters.get("warehouse"):
            closing_values["warehouse"] = filters.get("warehouse")
        
        closing_value_result = frappe.db.sql(closing_value_query, closing_values, as_dict=1)
        closing_value = flt(closing_value_result[0].value) if closing_value_result and closing_value_result[0].value else 0
        
        result.append({
            "item": item,
            "item_name": item_name,
            "opening_qty": opening_qty,
            "purchased_qty": purchased_qty,
            "purchase_value": purchase_value,
            "sold_qty": sold_qty,
            "sales_value": sales_value,
            "other_in_qty": other_in_qty,
            "other_out_qty": other_out_qty,
            "closing_qty": closing_qty,
            "closing_value": closing_value
        })
    
    return result

def get_chart(data):
    if not data:
        return None
    
    # Get top 10 items by movement (purchased + sold)
    sorted_data = sorted(data, key=lambda x: x.get("purchased_qty", 0) + x.get("sold_qty", 0), reverse=True)[:10]
    
    labels = [d.get("item_name") or d.get("item") for d in sorted_data]
    purchased = [d.get("purchased_qty", 0) for d in sorted_data]
    sold = [d.get("sold_qty", 0) for d in sorted_data]
    
    return {
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "name": _("Purchased"),
                    "values": purchased
                },
                {
                    "name": _("Sold"),
                    "values": sold
                }
            ]
        },
        "type": "bar",
        "colors": ["#28a745", "#dc3545"]
    }
