# Copyright (c) 2025, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
    if not filters:
        filters = {}
    
    columns = get_columns()
    data = get_data(filters)
    
    return columns, data

def get_columns():
    return [
        {
            "label": _("Supplier Name"),
            "fieldname": "supplier_name",
            "fieldtype": "Link",
            "options": "Supplier",
            "width": 180
        },
        {
            "label": _("Supplier Type"),
            "fieldname": "supplier_type",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Contact Person"),
            "fieldname": "contact_person",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("Phone Number"),
            "fieldname": "contact_number",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Mobile"),
            "fieldname": "mobile",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Email"),
            "fieldname": "email",
            "fieldtype": "Data",
            "width": 180
        },
        {
            "label": _("Wilaya"),
            "fieldname": "wilaya",
            "fieldtype": "Link",
            "options": "Wilaya",
            "width": 120
        },
        {
            "label": _("Commune"),
            "fieldname": "commune",
            "fieldtype": "Link",
            "options": "Commune",
            "width": 120
        },
        {
            "label": _("NIF"),
            "fieldname": "nif_number",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("RC Number"),
            "fieldname": "rc_number",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Status"),
            "fieldname": "status",
            "fieldtype": "Data",
            "width": 80
        }
    ]

def get_data(filters):
    conditions = get_conditions(filters)
    
    query = """
        SELECT 
            s.name as supplier_name,
            s.supplier_type,
            s.contact_person,
            s.contact_number,
            s.mobile,
            s.email,
            s.wilaya,
            s.commune,
            s.nif_number,
            s.rc_number,
            s.status
        FROM 
            `tabSupplier` s
        WHERE 
            1=1
            {conditions}
        ORDER BY 
            s.supplier_name
    """.format(conditions=conditions)
    
    data = frappe.db.sql(query, filters, as_dict=1)
    
    return data

def get_conditions(filters):
    conditions = ""
    
    if filters.get("supplier_type"):
        conditions += " AND s.supplier_type = %(supplier_type)s"
    
    if filters.get("wilaya"):
        conditions += " AND s.wilaya = %(wilaya)s"
    
    if filters.get("commune"):
        conditions += " AND s.commune = %(commune)s"
    
    if filters.get("status"):
        conditions += " AND s.status = %(status)s"
    else:
        # By default, show only active suppliers
        conditions += " AND s.status = 'Active'"
    
    return conditions

