# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate, formatdate


def execute(filters=None):
	"""Main report execution function"""
	if not filters:
		filters = {}
	
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart_data(data)
	summary = get_summary(data)
	
	return columns, data, None, chart, summary


def get_columns():
	"""Define report columns"""
	return [
		{
			"fieldname": "posting_date",
			"label": _("Date"),
			"fieldtype": "Date",
			"width": 100
		},
		{
			"fieldname": "pos_session",
			"label": _("POS Session"),
			"fieldtype": "Link",
			"options": "POS Session",
			"width": 150
		},
		{
			"fieldname": "invoice_name",
			"label": _("Invoice"),
			"fieldtype": "Link",
			"options": "POS Invoice",
			"width": 120
		},
		{
			"fieldname": "customer",
			"label": _("Customer"),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "item_code",
			"label": _("Item Code"),
			"fieldtype": "Link",
			"options": "Item",
			"width": 120
		},
		{
			"fieldname": "item_name",
			"label": _("Item Name"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "qty",
			"label": _("Qty"),
			"fieldtype": "Float",
			"width": 80
		},
		{
			"fieldname": "rate",
			"label": _("Rate"),
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"fieldname": "amount",
			"label": _("Amount"),
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"fieldname": "cost_price",
			"label": _("Cost Price"),
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"fieldname": "total_cost",
			"label": _("Total Cost"),
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"fieldname": "profit_amount",
			"label": _("Profit"),
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"fieldname": "profit_margin_percent",
			"label": _("Profit %"),
			"fieldtype": "Percent",
			"width": 100
		}
	]


def get_data(filters):
	"""Get report data based on filters"""
	conditions = get_conditions(filters)
	
	query = f"""
		SELECT 
			pi.posting_date,
			pi.pos_session,
			pi.name as invoice_name,
			pi.customer,
			pii.item_code,
			pii.item_name,
			pii.qty,
			pii.rate,
			pii.amount,
			pii.cost_price,
			(pii.cost_price * pii.qty) as total_cost,
			pii.profit_amount,
			pii.profit_margin_percent
		FROM `tabPOS Invoice` pi
		INNER JOIN `tabPOS Invoice Item` pii ON pi.name = pii.parent
		WHERE pi.docstatus = 1 {conditions}
		ORDER BY pi.posting_date DESC, pi.name, pii.idx
	"""
	
	return frappe.db.sql(query, filters, as_dict=1)


def get_conditions(filters):
	"""Build SQL conditions based on filters"""
	conditions = []
	
	if filters.get("from_date"):
		conditions.append("pi.posting_date >= %(from_date)s")
	
	if filters.get("to_date"):
		conditions.append("pi.posting_date <= %(to_date)s")
	
	if filters.get("pos_session"):
		conditions.append("pi.pos_session = %(pos_session)s")
	
	if filters.get("item_code"):
		conditions.append("pii.item_code = %(item_code)s")
	
	if filters.get("customer"):
		conditions.append("pi.customer = %(customer)s")
	
	return " AND " + " AND ".join(conditions) if conditions else ""


def get_chart_data(data):
	"""Generate chart data for profit analysis"""
	if not data:
		return None
	
	# Group data by date for chart
	date_wise_data = {}
	for row in data:
		date = row.posting_date
		if date not in date_wise_data:
			date_wise_data[date] = {
				"sales": 0,
				"cost": 0,
				"profit": 0
			}
		
		date_wise_data[date]["sales"] += flt(row.amount)
		date_wise_data[date]["cost"] += flt(row.total_cost)
		date_wise_data[date]["profit"] += flt(row.profit_amount)
	
	# Sort dates
	sorted_dates = sorted(date_wise_data.keys())
	
	return {
		"data": {
			"labels": [formatdate(date) for date in sorted_dates],
			"datasets": [
				{
					"name": "Sales",
					"values": [date_wise_data[date]["sales"] for date in sorted_dates]
				},
				{
					"name": "Cost",
					"values": [date_wise_data[date]["cost"] for date in sorted_dates]
				},
				{
					"name": "Profit",
					"values": [date_wise_data[date]["profit"] for date in sorted_dates]
				}
			]
		},
		"type": "line",
		"height": 300
	}


def get_summary(data):
	"""Generate summary statistics"""
	if not data:
		return []
	
	total_sales = sum(flt(row.amount) for row in data)
	total_cost = sum(flt(row.total_cost) for row in data)
	total_profit = sum(flt(row.profit_amount) for row in data)
	total_qty = sum(flt(row.qty) for row in data)
	
	overall_margin = (total_profit / total_sales * 100) if total_sales > 0 else 0
	
	return [
		{
			"value": total_sales,
			"label": _("Total Sales"),
			"datatype": "Currency"
		},
		{
			"value": total_cost,
			"label": _("Total Cost"),
			"datatype": "Currency"
		},
		{
			"value": total_profit,
			"label": _("Total Profit"),
			"datatype": "Currency"
		},
		{
			"value": overall_margin,
			"label": _("Overall Margin %"),
			"datatype": "Percent"
		},
		{
			"value": total_qty,
			"label": _("Total Quantity"),
			"datatype": "Float"
		},
		{
			"value": len(data),
			"label": _("Total Items Sold"),
			"datatype": "Int"
		}
	]