# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class POSInvoiceItem(Document):
	def validate(self):
		self.calculate_amount()
	
	def calculate_amount(self):
		"""Calculate line amount"""
		self.amount = flt(self.qty) * flt(self.rate) 