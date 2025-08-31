# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class POSProfile(Document):
	def validate(self):
		self.validate_default_profile()
		if self.payment_methods:
			self.validate_payment_methods()
	
	def validate_default_profile(self):
		"""Ensure only one default POS Profile exists"""
		if self.is_default:
			existing_default = frappe.db.get_value(
				"POS Profile", 
				{"is_default": 1, "name": ["!=", self.name]}, 
				"name"
			)
			if existing_default:
				frappe.throw(f"POS Profile {existing_default} is already set as default. Please uncheck 'Is Default' for it first.")
	
	def validate_payment_methods(self):
		"""Validate that payment methods are not duplicated"""
		# Check for duplicate payment methods
		payment_method_list = []
		for row in self.payment_methods:
			if row.payment_method in payment_method_list:
				frappe.throw(f"Payment Method {row.payment_method} is duplicated")
			payment_method_list.append(row.payment_method)

	@frappe.whitelist()
	def get_pos_profile_data(self):
		"""Get complete POS profile data for the POS interface"""
		return {
			"profile": self.as_dict(),
			"payment_methods": [pm.as_dict() for pm in self.payment_methods],
			"company_name": self.company_name,
			"warehouse_name": self.warehouse_name
		}

@frappe.whitelist()
def get_default_pos_profile():
	"""Get the default POS profile"""
	default_profile = frappe.db.get_value("POS Profile", {"is_default": 1}, "name")
	if default_profile:
		return frappe.get_doc("POS Profile", default_profile)
	else:
		# Return the first available profile
		first_profile = frappe.db.get_value("POS Profile", {}, "name")
		if first_profile:
			return frappe.get_doc("POS Profile", first_profile)
	return None 