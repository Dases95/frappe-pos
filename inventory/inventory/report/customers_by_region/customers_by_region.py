# Copyright (c) 2023, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
    if not filters:
        filters = {}
    
    columns = get_columns()
    data = get_data(filters)
    
    chart = get_chart_data(data)
    report_summary = get_report_summary(data)
    
    return columns, data, None, chart, report_summary

def get_columns():
    return [
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
            "label": _("Customer"),
            "fieldname": "customer",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 180
        },
        {
            "label": _("Customer Name"),
            "fieldname": "customer_name",
            "fieldtype": "Data",
            "width": 180
        },
        {
            "label": _("Customer Type"),
            "fieldname": "customer_type",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Contact Number"),
            "fieldname": "contact_number",
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
            c.wilaya, 
            c.commune,
            c.name as customer, 
            c.customer_name,
            c.customer_type,
            c.contact_number,
            c.email,
            c.status
        FROM 
            `tabCustomer` c
        WHERE 
            c.docstatus < 2
            {conditions}
        ORDER BY 
            c.wilaya, c.commune, c.customer_name
    """.format(conditions=conditions)
    
    data = frappe.db.sql(query, filters, as_dict=1)
    
    return data

def get_conditions(filters):
    conditions = ""
    
    if filters.get("wilaya"):
        conditions += " AND c.wilaya = %(wilaya)s"
    
    if filters.get("commune"):
        conditions += " AND c.commune = %(commune)s"
    
    if filters.get("customer_type"):
        conditions += " AND c.customer_type = %(customer_type)s"
    
    if filters.get("status"):
        conditions += " AND c.status = %(status)s"
    
    if filters.get("with_contact"):
        conditions += " AND c.contact_number IS NOT NULL AND c.contact_number != ''"
    
    if filters.get("with_email"):
        conditions += " AND c.email IS NOT NULL AND c.email != ''"
    
    return conditions

def get_chart_data(data):
    if not data:
        return None
    
    # Group data by wilaya and customer type
    wilaya_data = {}
    customer_types = set()
    
    for row in data:
        wilaya = row.get("wilaya") or "Not Specified"
        customer_type = row.get("customer_type") or "Not Specified"
        
        customer_types.add(customer_type)
        
        if wilaya not in wilaya_data:
            wilaya_data[wilaya] = {}
        
        if customer_type not in wilaya_data[wilaya]:
            wilaya_data[wilaya][customer_type] = 0
        
        wilaya_data[wilaya][customer_type] += 1
    
    # Sort wilayas by total customer count
    def get_total_count(wilaya_item):
        return sum(wilaya_item[1].values())
    
    sorted_wilaya_data = sorted(wilaya_data.items(), key=get_total_count, reverse=True)
    
    # Take top 10 wilayas for the chart
    top_wilayas = sorted_wilaya_data[:10]
    
    # Prepare chart data
    labels = [x[0] for x in top_wilayas]
    datasets = []
    
    # Sort customer types alphabetically
    sorted_customer_types = sorted(customer_types)
    
    colors = ["#5e64ff", "#743ee2", "#ff5858", "#ffa00a", "#29a3a3", "#383838", "#7578f6"]
    
    for i, customer_type in enumerate(sorted_customer_types):
        values = []
        for wilaya, type_counts in top_wilayas:
            values.append(type_counts.get(customer_type, 0))
        
        datasets.append({
            "name": customer_type,
            "values": values,
            "chartType": "bar"
        })
    
    chart = {
        "type": "bar",
        "data": {
            "labels": labels,
            "datasets": datasets
        },
        "colors": colors[:len(sorted_customer_types)],
        "title": _("Top 10 Wilayas by Customer Count and Type"),
        "height": 300,
        "axisOptions": {
            "xAxisMode": "tick",
            "yAxisMode": "tick"
        },
        "barOptions": {
            "stacked": 1
        }
    }
    
    return chart

def get_report_summary(data):
    if not data:
        return None
    
    total_customers = len(data)
    active_customers = len([d for d in data if d.get("status") == "Active"])
    inactive_customers = len([d for d in data if d.get("status") == "Inactive"])
    
    # Count by customer type
    customer_types = {}
    for row in data:
        ctype = row.get("customer_type") or "Not Specified"
        if ctype not in customer_types:
            customer_types[ctype] = 0
        customer_types[ctype] += 1
    
    # Get the most common customer type
    most_common_type = max(customer_types.items(), key=lambda x: x[1]) if customer_types else ("None", 0)
    
    # Count wilayas and communes
    unique_wilayas = set(row.get("wilaya") for row in data if row.get("wilaya"))
    unique_communes = set(row.get("commune") for row in data if row.get("commune"))
    
    return [
        {
            "value": total_customers,
            "label": _("Total Customers"),
            "datatype": "Int",
            "indicator": "blue"
        },
        {
            "value": active_customers,
            "label": _("Active Customers"),
            "datatype": "Int",
            "indicator": "green"
        },
        {
            "value": inactive_customers,
            "label": _("Inactive Customers"),
            "datatype": "Int",
            "indicator": "red"
        },
        {
            "value": len(unique_wilayas),
            "label": _("Wilayas Represented"),
            "datatype": "Int",
            "indicator": "gray"
        },
        {
            "value": len(unique_communes),
            "label": _("Communes Represented"),
            "datatype": "Int",
            "indicator": "gray"
        },
        {
            "value": most_common_type[0],
            "label": _("Most Common Type"),
            "datatype": "String",
            "indicator": "purple"
        }
    ] 