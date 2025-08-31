# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt

class POSClientTransaction(Document):
	def validate(self):
		self.validate_amount()
		self.validate_client()

	def validate_amount(self):
		"""Validate transaction amount"""
		if not self.amount or flt(self.amount) <= 0:
			frappe.throw(_("Transaction amount must be greater than zero"))

	def validate_client(self):
		"""Validate client exists and is active"""
		if self.client:
			client_status = frappe.db.get_value("POS Client", self.client, "status")
			if client_status != "Active":
				frappe.throw(_("Cannot create transaction for inactive client"))

	def on_submit(self):
		"""Update client balance when transaction is submitted"""
		pass  # Balance is updated in POS Client controller

	def on_cancel(self):
		"""Reverse client balance when transaction is cancelled"""
		pass  # Handle cancellation logic if needed