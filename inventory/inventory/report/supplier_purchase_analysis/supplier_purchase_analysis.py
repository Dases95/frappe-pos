import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
    if not filters:
        filters = {}
    
    columns = get_columns(filters)
    data = get_data(filters)
    chart = get_chart(data, filters)
    
    return columns, data, None, chart

def get_columns(filters):
    if filters.get("group_by") == "Item":
        return [
            {"label": _("Item"), "fieldname": "item", "fieldtype": "Link", "options": "Item", "width": 120},
            {"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 150},
            {"label": _("Supplier"), "fieldname": "supplier", "fieldtype": "Link", "options": "Supplier", "width": 120},
            {"label": _("Supplier Name"), "fieldname": "supplier_name", "fieldtype": "Data", "width": 150},
            {"label": _("Qty Purchased"), "fieldname": "qty_purchased", "fieldtype": "Float", "width": 110},
            {"label": _("Total Amount"), "fieldname": "total_amount", "fieldtype": "Currency", "width": 120},
            {"label": _("Avg Rate"), "fieldname": "avg_rate", "fieldtype": "Currency", "width": 100},
            {"label": _("Last Purchase"), "fieldname": "last_purchase_date", "fieldtype": "Date", "width": 110},
            {"label": _("Purchase Count"), "fieldname": "purchase_count", "fieldtype": "Int", "width": 110},
        ]
    else:
        return [
            {"label": _("Supplier"), "fieldname": "supplier", "fieldtype": "Link", "options": "Supplier", "width": 120},
            {"label": _("Supplier Name"), "fieldname": "supplier_name", "fieldtype": "Data", "width": 150},
            {"label": _("Total Items"), "fieldname": "total_items", "fieldtype": "Int", "width": 100},
            {"label": _("Qty Purchased"), "fieldname": "qty_purchased", "fieldtype": "Float", "width": 110},
            {"label": _("Total Amount"), "fieldname": "total_amount", "fieldtype": "Currency", "width": 120},
            {"label": _("Avg Order Value"), "fieldname": "avg_order_value", "fieldtype": "Currency", "width": 120},
            {"label": _("Purchase Count"), "fieldname": "purchase_count", "fieldtype": "Int", "width": 110},
            {"label": _("First Purchase"), "fieldname": "first_purchase_date", "fieldtype": "Date", "width": 110},
            {"label": _("Last Purchase"), "fieldname": "last_purchase_date", "fieldtype": "Date", "width": 110},
        ]

def get_data(filters):
    conditions = ["pr.docstatus = 1"]
    values = {}
    
    if filters.get("from_date"):
        conditions.append("pr.posting_date >= %(from_date)s")
        values["from_date"] = filters.get("from_date")
    
    if filters.get("to_date"):
        conditions.append("pr.posting_date <= %(to_date)s")
        values["to_date"] = filters.get("to_date")
    
    if filters.get("supplier"):
        conditions.append("pr.supplier = %(supplier)s")
        values["supplier"] = filters.get("supplier")
    
    if filters.get("item"):
        conditions.append("pri.item = %(item)s")
        values["item"] = filters.get("item")
    
    where_clause = " AND ".join(conditions)
    
    if filters.get("group_by") == "Item":
        # Group by Item and Supplier
        query = f"""
            SELECT 
                pri.item,
                pr.supplier,
                SUM(pri.quantity) as qty_purchased,
                SUM(pri.amount) as total_amount,
                AVG(pri.rate) as avg_rate,
                MAX(pr.posting_date) as last_purchase_date,
                COUNT(DISTINCT pr.name) as purchase_count
            FROM 
                "tabPurchase Receipt Item" pri
            INNER JOIN 
                "tabPurchase Receipt" pr ON pr.name = pri.parent
            WHERE 
                {where_clause}
            GROUP BY 
                pri.item, pr.supplier
            ORDER BY 
                SUM(pri.amount) DESC
        """
        
        result = frappe.db.sql(query, values=values, as_dict=1)
        
        for row in result:
            row["item_name"] = frappe.get_value("Item", row.item, "item_name") or ""
            row["supplier_name"] = frappe.get_value("Supplier", row.supplier, "supplier_name") or ""
        
        return result
    else:
        # Group by Supplier
        query = f"""
            SELECT 
                pr.supplier,
                COUNT(DISTINCT pri.item) as total_items,
                SUM(pri.quantity) as qty_purchased,
                SUM(pri.amount) as total_amount,
                COUNT(DISTINCT pr.name) as purchase_count,
                MIN(pr.posting_date) as first_purchase_date,
                MAX(pr.posting_date) as last_purchase_date
            FROM 
                "tabPurchase Receipt Item" pri
            INNER JOIN 
                "tabPurchase Receipt" pr ON pr.name = pri.parent
            WHERE 
                {where_clause}
            GROUP BY 
                pr.supplier
            ORDER BY 
                SUM(pri.amount) DESC
        """
        
        result = frappe.db.sql(query, values=values, as_dict=1)
        
        for row in result:
            row["supplier_name"] = frappe.get_value("Supplier", row.supplier, "supplier_name") or ""
            row["avg_order_value"] = flt(row.total_amount) / row.purchase_count if row.purchase_count else 0
        
        return result

def get_chart(data, filters):
    if not data:
        return None
    
    # Get top 10 by total amount
    sorted_data = sorted(data, key=lambda x: x.get("total_amount", 0), reverse=True)[:10]
    
    if filters.get("group_by") == "Item":
        labels = [f"{d.get('item_name') or d.get('item')} ({d.get('supplier')})" for d in sorted_data]
    else:
        labels = [d.get("supplier_name") or d.get("supplier") for d in sorted_data]
    
    amounts = [d.get("total_amount", 0) for d in sorted_data]
    
    return {
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "name": _("Purchase Amount"),
                    "values": amounts
                }
            ]
        },
        "type": "bar",
        "colors": ["#5e64ff"]
    }
