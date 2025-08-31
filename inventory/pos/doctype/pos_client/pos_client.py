# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, now

class POSClient(Document):
	def validate(self):
		self.set_full_name()
		self.validate_credit_limit()
		self.validate_email()
		self.validate_phone()

	def set_full_name(self):
		"""Set full name from first and last name"""
		if self.first_name and self.last_name:
			self.full_name = f"{self.first_name} {self.last_name}"
		elif self.first_name:
			self.full_name = self.first_name
		elif self.last_name:
			self.full_name = self.last_name

	def validate_credit_limit(self):
		"""Validate credit limit settings"""
		if self.allow_credit and not self.credit_limit:
			frappe.throw(_("Credit Limit is required when Allow Credit Payment is enabled"))
		
		if self.credit_limit and self.credit_limit < 0:
			frappe.throw(_("Credit Limit cannot be negative"))

	def validate_email(self):
		"""Validate email format"""
		if self.email:
			import re
			email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
			if not re.match(email_pattern, self.email):
				frappe.throw(_("Please enter a valid email address"))

	def validate_phone(self):
		"""Validate phone number format"""
		if self.phone:
			import re
			# Allow various phone formats
			phone_pattern = r'^[\+]?[0-9\s\-\(\)]{10,}$'
			if not re.match(phone_pattern, self.phone):
				frappe.throw(_("Please enter a valid phone number"))

	def can_make_credit_purchase(self, amount):
		"""Check if client can make a credit purchase for given amount"""
		if not self.allow_credit:
			return False, _("Credit payment not allowed for this client")
		
		if self.status != "Active":
			return False, _("Client account is not active")
		
		available_credit = flt(self.credit_limit) - flt(self.current_balance)
		if flt(amount) > available_credit:
			return False, _(f"Insufficient credit limit. Available: {available_credit:.2f} DZD")
		
		return True, ""

	def add_credit_transaction(self, amount, transaction_type="Sale", reference_doc=None):
		"""Add a credit transaction and update balance"""
		if transaction_type == "Sale":
			self.current_balance = flt(self.current_balance) + flt(amount)
		elif transaction_type == "Payment":
			self.current_balance = flt(self.current_balance) - flt(amount)
		
		self.last_transaction_date = now()
		self.save(ignore_permissions=True)
		
		# Create transaction log
		self.create_transaction_log(amount, transaction_type, reference_doc)

	def create_transaction_log(self, amount, transaction_type, reference_doc=None):
		"""Create a transaction log entry"""
		try:
			transaction_log = frappe.get_doc({
				"doctype": "POS Client Transaction",
				"client": self.name,
				"transaction_date": now(),
				"transaction_type": transaction_type,
				"amount": amount,
				"balance_after": self.current_balance,
				"reference_document": reference_doc
			})
			transaction_log.insert(ignore_permissions=True)
		except Exception as e:
			frappe.log_error(f"Error creating transaction log: {str(e)}")

	@frappe.whitelist()
	def get_credit_summary(self):
		"""Get credit summary for the client"""
		available_credit = flt(self.credit_limit) - flt(self.current_balance)
		return {
			"credit_limit": self.credit_limit,
			"current_balance": self.current_balance,
			"available_credit": available_credit,
			"allow_credit": self.allow_credit,
			"status": self.status
		}

@frappe.whitelist()
def search_pos_clients(search_term, limit=10):
	"""Search POS clients for autocomplete"""
	try:
		filters = [
			["status", "=", "Active"]
		]
		
		if search_term:
			filters.append([
				"full_name", "like", f"%{search_term}%"
			])
		
		clients = frappe.get_all(
			"POS Client",
			filters=filters,
			fields=["name", "client_code", "full_name", "phone", "allow_credit", "current_balance", "credit_limit"],
			limit=limit,
			order_by="full_name"
		)
		
		# Add calculated available credit
		for client in clients:
			client["available_credit"] = flt(client.get("credit_limit", 0)) - flt(client.get("current_balance", 0))
		
		return clients
		
	except Exception as e:
		frappe.log_error(f"Error in search_pos_clients: {str(e)}")
		return []

@frappe.whitelist()
def get_client_details(client_name):
	"""Get detailed client information"""
	try:
		client = frappe.get_doc("POS Client", client_name)
		return client.get_credit_summary()
	except Exception as e:
		frappe.log_error(f"Error in get_client_details: {str(e)}")
		return None

@frappe.whitelist()
def validate_credit_purchase(client_name, amount):
	"""Validate if a credit purchase can be made"""
	try:
		client = frappe.get_doc("POS Client", client_name)
		can_purchase, message = client.can_make_credit_purchase(amount)
		return {
			"can_purchase": can_purchase,
			"message": message
		}
	except Exception as e:
		frappe.log_error(f"Error in validate_credit_purchase: {str(e)}")
		return {
			"can_purchase": False,
			"message": "Error validating credit purchase"
		}