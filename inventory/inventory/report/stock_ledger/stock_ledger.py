import frappe
from frappe import _

def execute(filters=None):
    if not filters:
        filters = {}

    # Initialize filters if not provided
    filters.setdefault('item_code', '')
    filters.setdefault('warehouse', '')
    filters.setdefault('from_date', '')
    filters.setdefault('to_date', '')

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
        values['item_code'] = filters['item_code']
    
    if filters.get('warehouse'):
        conditions.append("warehouse = %(warehouse)s")
        values['warehouse'] = filters['warehouse']
    
    if filters.get('from_date'):
        conditions.append("posting_date >= %(from_date)s")
        values['from_date'] = filters['from_date']
    
    if filters.get('to_date'):
        conditions.append("posting_date <= %(to_date)s")
        values['to_date'] = filters['to_date']
    
    # Construct the WHERE clause
    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
    
    # Query to get stock ledger entries
    query = f"""
        SELECT 
            posting_date,
            posting_time,
            item,
            warehouse,
            batch_no,
            actual_qty,
            voucher_type,
            voucher_no
        FROM 
            `tabStock Ledger Entry`
        {where_clause}
        ORDER BY 
            posting_date, posting_time, name
    """
    
    result = frappe.db.sql(query, values=values, as_dict=1)
    
    # Calculate running balance for each unique combination of item, warehouse, and batch
    balance_tracker = {}
    for row in result:
        # Create a unique key to track balances for each item/warehouse/batch
        key = (row['item'], row['warehouse'], row['batch_no'])
        if key not in balance_tracker:
            balance_tracker[key] = 0
        
        # Update balance for the current row
        balance_tracker[key] += row['actual_qty']
        row['balance_qty'] = balance_tracker[key]
        
        # Add item name
        row['item_name'] = frappe.get_value("Item", row['item'], "item_name") or ""
    
    return result
