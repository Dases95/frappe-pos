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
    if not filters.get('batch_id'):
        filters['batch_id'] = ''

    # Define columns for the report
    columns = [
        {"label": _("Item"), "fieldname": "item", "fieldtype": "Link", "options": "Item", "width": 120},
        {"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 120},
        {"label": _("Warehouse"), "fieldname": "warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 120},
        {"label": _("Batch"), "fieldname": "batch_no", "fieldtype": "Link", "options": "Batch", "width": 100},
        {"label": _("Available Qty"), "fieldname": "balance_qty", "fieldtype": "Float", "width": 100},
        {"label": _("Valuation Rate"), "fieldname": "valuation_rate", "fieldtype": "Currency", "width": 110},
        {"label": _("Value"), "fieldname": "value", "fieldtype": "Currency", "width": 110}
    ]

    # Get data from Stock Ledger Entry
    data = get_stock_balance_data(filters)
    
    return columns, data

def get_stock_balance_data(filters):
    conditions = []
    values = {}
    
    if filters.get('item_code'):
        conditions.append("item = %(item_code)s")
        values['item_code'] = filters.get('item_code')
    
    if filters.get('warehouse'):
        conditions.append("warehouse = %(warehouse)s")
        values['warehouse'] = filters.get('warehouse')
    
    if filters.get('batch_id'):
        conditions.append("batch_no = %(batch_id)s")
        values['batch_id'] = filters.get('batch_id')
    
    # Construct the WHERE clause
    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)
    
    # Query to get stock balance with correct valuation calculation
    # Using SUM(actual_qty * valuation_rate) / SUM(actual_qty) for weighted average
    query = f"""
        SELECT 
            item, 
            warehouse,
            batch_no,
            SUM(actual_qty) as balance_qty,
            SUM(actual_qty * valuation_rate) as total_value
        FROM 
            "tabStock Ledger Entry" 
        {where_clause}
        GROUP BY 
            item, warehouse, batch_no
        HAVING 
            SUM(actual_qty) != 0
        ORDER BY 
            item, warehouse, batch_no
    """
    
    result = frappe.db.sql(query, values=values, as_dict=1)
    
    # Enhance the data with additional information
    for row in result:
        # Get item name
        item_name = frappe.get_value("Item", row.item, "item_name")
        row.item_name = item_name or ""
        
        # Calculate weighted average valuation rate
        if row.balance_qty and row.total_value:
            row.valuation_rate = row.total_value / row.balance_qty
        else:
            row.valuation_rate = 0
        
        # Calculate value
        row.value = row.total_value if row.total_value else 0
    
    return result 