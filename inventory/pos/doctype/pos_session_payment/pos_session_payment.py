# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe.model.document import Document
from frappe.utils import flt


class POSSessionPayment(Document):
	def validate(self):
		self.calculate_difference()
	
	def calculate_difference(self):
		"""Calculate difference between expected and actual amount"""
		self.difference = flt(self.actual_amount) - flt(self.expected_amount) 