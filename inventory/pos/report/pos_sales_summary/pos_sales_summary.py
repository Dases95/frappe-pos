# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {
            "label": _("Date"),
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "width": 100
        },
        {
            "label": _("Invoice"),
            "fieldname": "name",
            "fieldtype": "Link",
            "options": "POS Invoice",
            "width": 120
        },
        {
            "label": _("Customer"),
            "fieldname": "customer",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 150
        },
        {
            "label": _("POS Profile"),
            "fieldname": "pos_profile",
            "fieldtype": "Link",
            "options": "POS Profile",
            "width": 120
        },
        {
            "label": _("User"),
            "fieldname": "user",
            "fieldtype": "Data",
            "width": 100
        },
        {
            "label": _("Total Qty"),
            "fieldname": "total_qty",
            "fieldtype": "Float",
            "width": 100
        },
        {
            "label": _("Net Total"),
            "fieldname": "net_total",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": _("Grand Total"),
            "fieldname": "grand_total",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": _("Paid Amount"),
            "fieldname": "paid_amount",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": _("Status"),
            "fieldname": "status",
            "fieldtype": "Data",
            "width": 100
        }
    ]


def get_data(filters):
    conditions = []
    values = []
    
    if filters.get("from_date"):
        conditions.append("posting_date >= %s")
        values.append(filters.get("from_date"))
    
    if filters.get("to_date"):
        conditions.append("posting_date <= %s")
        values.append(filters.get("to_date"))
    
    if filters.get("pos_profile"):
        conditions.append("pos_profile = %s")
        values.append(filters.get("pos_profile"))
    
    if filters.get("user"):
        conditions.append("owner = %s")
        values.append(filters.get("user"))
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    query = f"""
        SELECT 
            pi.posting_date,
            pi.name,
            pi.customer,
            pi.pos_profile,
            pi.owner as user,
            pi.total_qty,
            pi.net_total,
            pi.grand_total,
            pi.paid_amount,
            pi.status
        FROM `tabPOS Invoice` pi
        WHERE pi.docstatus = 1 AND {where_clause}
        ORDER BY pi.posting_date DESC, pi.creation DESC
    """
    
    return frappe.db.sql(query, values, as_dict=1) 