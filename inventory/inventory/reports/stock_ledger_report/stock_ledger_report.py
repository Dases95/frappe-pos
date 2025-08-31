import frappe
from frappe import _

def execute(filters=None):
    if not filters:
        filters = {}

    # Initialize filters if not provided
    if not filters.get('item_code'):
        filters['item_code'] = ''
    if not filters.get('warehouse'):
        filters['warehouse'] = ''
    if not filters.get('from_date'):
        filters['from_date'] = ''
    if not filters.get('to_date'):
        filters['to_date'] = ''

    # Define columns for the report
    columns = [
        {"label": _("Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
        {"label": _("Time"), "fieldname": "posting_time", "fieldtype": "Time", "width": 90},
        {"label": _("Item"), "fieldname": "item", "fieldtype": "Link", "options": "Item", "width": 120},
        {"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 120},
        {"label": _("Warehouse"), "fieldname": "warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 120},
        {"label": _("Batch"), "fieldname": "batch_no", "fieldtype": "Link", "options": "Batch", "width": 100},
        {"label": _("Qty"), "fieldname": "actual_qty", "fieldtype": "Float", "width": 100},
        {"label": _("Balance Qty"), "fieldname": "balance_qty", "fieldtype": "Float", "width": 100},
        {"label": _("Rate"), "fieldname": "valuation_rate", "fieldtype": "Currency", "width": 100},
        {"label": _("Value"), "fieldname": "stock_value", "fieldtype": "Currency", "width": 120},
        {"label": _("Value Difference"), "fieldname": "stock_value_difference", "fieldtype": "Currency", "width": 120},
        {"label": _("Voucher Type"), "fieldname": "voucher_type", "fieldtype": "Data", "width": 120},
        {"label": _("Voucher No"), "fieldname": "voucher_no", "fieldtype": "Dynamic Link", "options": "voucher_type", "width": 120}
    ]

    # Get data from Stock Ledger Entry
    data = get_stock_ledger_data(filters)
    
    return columns, data

def get_stock_ledger_data(filters):
    conditions = []
    values = {}
    
    if filters.get('item_code'):
        conditions.append("item = %(item_code)s")
        values['item_code'] = filters.get('item_code')
    
    if filters.get('warehouse'):
        conditions.append("warehouse = %(warehouse)s")
        values['warehouse'] = filters.get('warehouse')
    
    if filters.get('from_date'):
        conditions.append("posting_date >= %(from_date)s")
        values['from_date'] = filters.get('from_date')
    
    if filters.get('to_date'):
        conditions.append("posting_date <= %(to_date)s")
        values['to_date'] = filters.get('to_date')
    
    # Construct the WHERE clause
    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)
    
    # Query to get stock ledger entries
    query = f"""
        SELECT 
            posting_date,
            posting_time,
            item,
            warehouse,
            batch_no,
            actual_qty,
            valuation_rate,
            stock_value_difference,
            voucher_type,
            voucher_no
        FROM 
            `tabStock Ledger Entry` 
        {where_clause}
        ORDER BY 
            item, warehouse, posting_date, posting_time
    """
    
    result = frappe.db.sql(query, values=values, as_dict=1)
    
    # Group entries by item and warehouse to calculate running balances correctly
    grouped_data = {}
    for row in result:
        key = f"{row.item}::{row.warehouse}"
        if key not in grouped_data:
            grouped_data[key] = []
        grouped_data[key].append(row)
    
    final_data = []
    for key, entries in grouped_data.items():
        # Calculate running balance and valuation for each item-warehouse combination
        balance_qty = 0
        stock_value = 0
        
        for row in entries:
            # Get item name
            item_name = frappe.get_value("Item", row.item, "item_name")
            row.item_name = item_name or ""
            
            # Update balance quantity
            balance_qty += row.actual_qty
            row.balance_qty = balance_qty
            
            # Update stock value with the value difference
            stock_value_difference = row.stock_value_difference or 0
            stock_value += stock_value_difference
            row.stock_value = stock_value
            
            # Calculate weighted average valuation rate
            if balance_qty > 0:
                # Only calculate new valuation rate for positive balances
                row.valuation_rate = stock_value / balance_qty
            elif balance_qty == 0:
                # If balance is zero, there's no valuation
                row.valuation_rate = 0
            # For negative balances, keep the existing valuation rate
            
            final_data.append(row)
    
    # Sort the final data by date and time
    final_data.sort(key=lambda x: (x.posting_date, x.posting_time))
    
    return final_data 