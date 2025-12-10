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
        {"label": _("Qty Sold"), "fieldname": "qty_sold", "fieldtype": "Float", "width": 100},
        {"label": _("Sales Amount"), "fieldname": "sales_amount", "fieldtype": "Currency", "width": 120},
        {"label": _("Cost Amount"), "fieldname": "cost_amount", "fieldtype": "Currency", "width": 120},
        {"label": _("Gross Profit"), "fieldname": "gross_profit", "fieldtype": "Currency", "width": 120},
        {"label": _("Profit %"), "fieldname": "profit_percent", "fieldtype": "Percent", "width": 100},
        {"label": _("Avg Selling Price"), "fieldname": "avg_selling_price", "fieldtype": "Currency", "width": 120},
        {"label": _("Avg Cost Price"), "fieldname": "avg_cost_price", "fieldtype": "Currency", "width": 120},
    ]

def get_data(filters):
    conditions = ["dn.docstatus = 1"]
    values = {}
    
    if filters.get("from_date"):
        conditions.append("dn.delivery_date >= %(from_date)s")
        values["from_date"] = filters.get("from_date")
    
    if filters.get("to_date"):
        conditions.append("dn.delivery_date <= %(to_date)s")
        values["to_date"] = filters.get("to_date")
    
    if filters.get("item"):
        conditions.append("dni.item = %(item)s")
        values["item"] = filters.get("item")
    
    if filters.get("customer"):
        conditions.append("dn.customer = %(customer)s")
        values["customer"] = filters.get("customer")
    
    where_clause = " AND ".join(conditions)
    
    # Get sales data from Delivery Note
    query = f"""
        SELECT 
            dni.item,
            SUM(dni.quantity) as qty_sold,
            SUM(dni.amount) as sales_amount
        FROM 
            "tabDelivery Note Item" dni
        INNER JOIN 
            "tabDelivery Note" dn ON dn.name = dni.parent
        WHERE 
            {where_clause}
        GROUP BY 
            dni.item
        ORDER BY 
            SUM(dni.amount) DESC
    """
    
    sales_data = frappe.db.sql(query, values=values, as_dict=1)
    
    result = []
    for row in sales_data:
        item = row.item
        qty_sold = flt(row.qty_sold)
        sales_amount = flt(row.sales_amount)
        
        # Get item details
        item_doc = frappe.get_cached_doc("Item", item)
        item_name = item_doc.item_name if item_doc else ""
        
        # Calculate cost based on valuation rate from Stock Ledger Entry
        # Get the average valuation rate for this item during the period
        cost_data = get_item_cost(item, filters)
        cost_amount = flt(cost_data.get("total_cost", 0))
        avg_cost_price = flt(cost_data.get("avg_cost", 0))
        
        # If no cost data from stock ledger, use item's valuation rate
        if cost_amount == 0 and qty_sold > 0:
            valuation_rate = flt(item_doc.valuation_rate) if item_doc else 0
            cost_amount = qty_sold * valuation_rate
            avg_cost_price = valuation_rate
        
        # Calculate profit
        gross_profit = sales_amount - cost_amount
        profit_percent = (gross_profit / sales_amount * 100) if sales_amount > 0 else 0
        avg_selling_price = (sales_amount / qty_sold) if qty_sold > 0 else 0
        
        result.append({
            "item": item,
            "item_name": item_name,
            "qty_sold": qty_sold,
            "sales_amount": sales_amount,
            "cost_amount": cost_amount,
            "gross_profit": gross_profit,
            "profit_percent": profit_percent,
            "avg_selling_price": avg_selling_price,
            "avg_cost_price": avg_cost_price
        })
    
    return result

def get_item_cost(item, filters):
    """Get item cost from Stock Ledger Entry for outgoing transactions (Delivery Notes)"""
    conditions = [
        "item = %(item)s",
        "voucher_type = 'Delivery Note'",
        "actual_qty < 0",
        "is_cancelled = 0"
    ]
    values = {"item": item}
    
    if filters.get("from_date"):
        conditions.append("posting_date >= %(from_date)s")
        values["from_date"] = filters.get("from_date")
    
    if filters.get("to_date"):
        conditions.append("posting_date <= %(to_date)s")
        values["to_date"] = filters.get("to_date")
    
    where_clause = " AND ".join(conditions)
    
    query = f"""
        SELECT 
            SUM(ABS(actual_qty) * valuation_rate) as total_cost,
            AVG(valuation_rate) as avg_cost
        FROM 
            "tabStock Ledger Entry"
        WHERE 
            {where_clause}
    """
    
    result = frappe.db.sql(query, values=values, as_dict=1)
    
    if result and result[0]:
        return {
            "total_cost": flt(result[0].get("total_cost", 0)),
            "avg_cost": flt(result[0].get("avg_cost", 0))
        }
    
    return {"total_cost": 0, "avg_cost": 0}

def get_chart(data):
    if not data:
        return None
    
    # Get top 10 items by profit
    sorted_data = sorted(data, key=lambda x: x.get("gross_profit", 0), reverse=True)[:10]
    
    labels = [d.get("item_name") or d.get("item") for d in sorted_data]
    profit_values = [d.get("gross_profit", 0) for d in sorted_data]
    
    return {
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "name": _("Gross Profit"),
                    "values": profit_values
                }
            ]
        },
        "type": "bar",
        "colors": ["#5e64ff"]
    }
