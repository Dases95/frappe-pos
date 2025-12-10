// Copyright (c) 2025, Your Company and contributors
// For license information, please see license.txt

frappe.query_reports["Supplier Directory"] = {
	"filters": [
		{
			"fieldname": "supplier_type",
			"label": __("Supplier Type"),
			"fieldtype": "Select",
			"options": "\nManufacturer\nWholesaler\nDistributor\nImporter\nService Provider\nOther"
		},
		{
			"fieldname": "wilaya",
			"label": __("Wilaya"),
			"fieldtype": "Link",
			"options": "Wilaya"
		},
		{
			"fieldname": "commune",
			"label": __("Commune"),
			"fieldtype": "Link",
			"options": "Commune"
		},
		{
			"fieldname": "status",
			"label": __("Status"),
			"fieldtype": "Select",
			"options": "\nActive\nInactive\nBlocked",
			"default": "Active"
		}
	]
};

