# Copyright (c) 2025, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
    if not filters:
        filters = {}
    
    columns = get_columns(filters)
    data = get_data(filters)
    chart = get_chart(data, filters)
    summary = get_report_summary(data)
    
    return columns, data, None, chart, summary

def get_columns(filters):
    if filters.get("group_by") == "Item":
        return [
            {"label": _("Item"), "fieldname": "item", "fieldtype": "Link", "options": "Item", "width": 120},
            {"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 150},
            {"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 120},
            {"label": _("Customer Name"), "fieldname": "customer_name", "fieldtype": "Data", "width": 150},
            {"label": _("Qty Sold"), "fieldname": "qty_sold", "fieldtype": "Float", "width": 110},
            {"label": _("Total Amount"), "fieldname": "total_amount", "fieldtype": "Currency", "width": 120},
            {"label": _("Avg Rate"), "fieldname": "avg_rate", "fieldtype": "Currency", "width": 100},
            {"label": _("Last Sale"), "fieldname": "last_sale_date", "fieldtype": "Date", "width": 110},
            {"label": _("Sale Count"), "fieldname": "sale_count", "fieldtype": "Int", "width": 110},
        ]
    else:
        return [
            {"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 120},
            {"label": _("Customer Name"), "fieldname": "customer_name", "fieldtype": "Data", "width": 150},
            {"label": _("Customer Type"), "fieldname": "customer_type", "fieldtype": "Data", "width": 100},
            {"label": _("Wilaya"), "fieldname": "wilaya", "fieldtype": "Link", "options": "Wilaya", "width": 100},
            {"label": _("Total Items"), "fieldname": "total_items", "fieldtype": "Int", "width": 100},
            {"label": _("Qty Sold"), "fieldname": "qty_sold", "fieldtype": "Float", "width": 110},
            {"label": _("Total Amount"), "fieldname": "total_amount", "fieldtype": "Currency", "width": 120},
            {"label": _("Avg Order Value"), "fieldname": "avg_order_value", "fieldtype": "Currency", "width": 120},
            {"label": _("Sale Count"), "fieldname": "sale_count", "fieldtype": "Int", "width": 110},
            {"label": _("First Sale"), "fieldname": "first_sale_date", "fieldtype": "Date", "width": 110},
            {"label": _("Last Sale"), "fieldname": "last_sale_date", "fieldtype": "Date", "width": 110},
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
    
    if filters.get("customer"):
        conditions.append("dn.customer = %(customer)s")
        values["customer"] = filters.get("customer")
    
    if filters.get("item"):
        conditions.append("dni.item = %(item)s")
        values["item"] = filters.get("item")
    
    if filters.get("wilaya"):
        conditions.append("c.wilaya = %(wilaya)s")
        values["wilaya"] = filters.get("wilaya")
    
    where_clause = " AND ".join(conditions)
    
    if filters.get("group_by") == "Item":
        # Group by Item and Customer
        query = f"""
            SELECT 
                dni.item,
                dn.customer,
                SUM(dni.quantity) as qty_sold,
                SUM(dni.amount) as total_amount,
                AVG(dni.rate) as avg_rate,
                MAX(dn.delivery_date) as last_sale_date,
                COUNT(DISTINCT dn.name) as sale_count
            FROM 
                "tabDelivery Note Item" dni
            INNER JOIN 
                "tabDelivery Note" dn ON dn.name = dni.parent
            LEFT JOIN
                "tabCustomer" c ON c.name = dn.customer
            WHERE 
                {where_clause}
            GROUP BY 
                dni.item, dn.customer
            ORDER BY 
                SUM(dni.amount) DESC
        """
        
        result = frappe.db.sql(query, values=values, as_dict=1)
        
        for row in result:
            row["item_name"] = frappe.get_value("Item", row.item, "item_name") or ""
            row["customer_name"] = frappe.get_value("Customer", row.customer, "customer_name") or ""
        
        return result
    else:
        # Group by Customer
        query = f"""
            SELECT 
                dn.customer,
                COUNT(DISTINCT dni.item) as total_items,
                SUM(dni.quantity) as qty_sold,
                SUM(dni.amount) as total_amount,
                COUNT(DISTINCT dn.name) as sale_count,
                MIN(dn.delivery_date) as first_sale_date,
                MAX(dn.delivery_date) as last_sale_date
            FROM 
                "tabDelivery Note Item" dni
            INNER JOIN 
                "tabDelivery Note" dn ON dn.name = dni.parent
            LEFT JOIN
                "tabCustomer" c ON c.name = dn.customer
            WHERE 
                {where_clause}
            GROUP BY 
                dn.customer
            ORDER BY 
                SUM(dni.amount) DESC
        """
        
        result = frappe.db.sql(query, values=values, as_dict=1)
        
        for row in result:
            customer_data = frappe.db.get_value("Customer", row.customer, 
                ["customer_name", "customer_type", "wilaya"], as_dict=1)
            if customer_data:
                row["customer_name"] = customer_data.customer_name or ""
                row["customer_type"] = customer_data.customer_type or ""
                row["wilaya"] = customer_data.wilaya or ""
            row["avg_order_value"] = flt(row.total_amount) / row.sale_count if row.sale_count else 0
        
        return result

def get_chart(data, filters):
    if not data:
        return None
    
    # Get top 10 by total amount
    sorted_data = sorted(data, key=lambda x: x.get("total_amount", 0), reverse=True)[:10]
    
    if filters.get("group_by") == "Item":
        labels = [f"{d.get('item_name') or d.get('item')} ({d.get('customer')})" for d in sorted_data]
    else:
        labels = [d.get("customer_name") or d.get("customer") for d in sorted_data]
    
    amounts = [d.get("total_amount", 0) for d in sorted_data]
    
    return {
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "name": _("Sales Amount"),
                    "values": amounts
                }
            ]
        },
        "type": "bar",
        "colors": ["#29a3a3"],
        "height": 300
    }

def get_report_summary(data):
    if not data:
        return None
    
    total_customers = len(data)
    total_amount = sum(flt(d.get("total_amount", 0)) for d in data)
    total_qty = sum(flt(d.get("qty_sold", 0)) for d in data)
    avg_order_value = total_amount / total_customers if total_customers else 0
    
    return [
        {
            "value": total_customers,
            "label": _("Total Customers"),
            "datatype": "Int",
            "indicator": "blue"
        },
        {
            "value": total_amount,
            "label": _("Total Sales"),
            "datatype": "Currency",
            "indicator": "green"
        },
        {
            "value": total_qty,
            "label": _("Total Quantity Sold"),
            "datatype": "Float",
            "indicator": "gray"
        },
        {
            "value": avg_order_value,
            "label": _("Avg Order Value"),
            "datatype": "Currency",
            "indicator": "purple"
        }
    ]

