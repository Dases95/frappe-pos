# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, now_datetime, getdate, nowtime


class POSInvoice(Document):
	def validate(self):
		self.validate_pos_session()
		self.validate_customer()
		self.calculate_totals()
		self.validate_payments()
		self.set_status()

	def before_save(self):
		if not self.posting_time:
			self.posting_time = nowtime()

	def before_submit(self):
		self.update_stock()
		self.status = "Paid"

	def on_cancel(self):
		self.status = "Cancelled"
		self.update_stock(cancel=True)

	def validate_pos_session(self):
		"""Validate POS session is open"""
		if self.pos_session:
			session_status = frappe.db.get_value("POS Session", self.pos_session, "status")
			if session_status not in ["Open"]:
				frappe.throw(_("POS Session must be Open to create transactions"))

	def validate_customer(self):
		"""Validate customer - simplified for standalone inventory app"""
		if not self.customer:
			self.customer = "Walk-in Customer"

	def calculate_totals(self):
		"""Calculate invoice totals including profit analysis"""
		self.total_qty = 0
		self.net_total = 0
		self.total_cost = 0
		self.total_profit = 0
		
		for item in self.items:
			# Calculate amount for each item
			item.amount = flt(item.qty) * flt(item.rate)
			
			# Get cost price from item's valuation rate
			item_cost = frappe.db.get_value("Item", item.item_code, "valuation_rate") or 0
			item.cost_price = flt(item_cost)
			
			# Calculate profit for this item
			total_cost_for_item = flt(item.cost_price) * flt(item.qty)
			item.profit_amount = flt(item.amount) - total_cost_for_item
			
			# Calculate profit margin percentage
			if flt(item.amount) > 0:
				item.profit_margin_percent = (flt(item.profit_amount) / flt(item.amount)) * 100
			else:
				item.profit_margin_percent = 0
			
			# Add to totals
			self.total_qty += flt(item.qty)
			self.net_total += flt(item.amount)
			self.total_cost += total_cost_for_item
			self.total_profit += flt(item.profit_amount)
		
		# Calculate overall profit margin
		if self.net_total > 0:
			self.profit_margin_percent = (self.total_profit / self.net_total) * 100
		else:
			self.profit_margin_percent = 0
		
		self.grand_total = self.net_total
		
		# Apply rounding
		if self.net_total != self.grand_total:
			self.rounding_adjustment = self.grand_total - self.net_total
		
		# Set rounded total
		self.rounded_total = round(self.grand_total)
		if self.rounded_total != self.grand_total:
			self.rounding_adjustment = self.rounded_total - self.grand_total
			self.grand_total = self.rounded_total

	def validate_payments(self):
		"""Validate payment details"""
		if not self.payments:
			frappe.throw(_("At least one payment entry is required"))
		
		total_payment = sum(flt(payment.amount) for payment in self.payments)
		self.paid_amount = total_payment
		
		# Calculate change
		self.change_amount = max(0, self.paid_amount - self.grand_total)
		
		# Validate sufficient payment
		if self.paid_amount < self.grand_total and not self.is_return:
			frappe.throw(_("Paid amount cannot be less than Grand Total"))

	def set_status(self):
		"""Set invoice status based on payment"""
		if self.docstatus == 0:
			self.status = "Draft"
		elif self.docstatus == 1:
			if self.paid_amount >= self.grand_total:
				self.status = "Paid"
			else:
				self.status = "Unpaid"
		elif self.docstatus == 2:
			self.status = "Cancelled"

	def update_stock(self, cancel=False):
		"""Update stock levels by creating stock ledger entries"""
		default_warehouse = self.warehouse or self.get_default_warehouse()
		for item in self.items:
			self.create_stock_ledger_entry(
				item.item_code,
				default_warehouse,
				item.qty,
				item.rate,
				cancel
			)

	def create_stock_ledger_entry(self, item_code, warehouse, qty, rate, cancel=False):
		"""Create stock ledger entry for POS invoice item"""
		if not warehouse:
			warehouse = self.get_default_warehouse()
		if not warehouse:
			return
		
		# Create stock ledger entry
		sle = frappe.new_doc("Stock Ledger Entry")
		sle.item = item_code
		sle.warehouse = warehouse
		sle.posting_date = self.posting_date
		sle.posting_time = self.posting_time
		sle.voucher_type = "POS Invoice"
		sle.voucher_no = self.name
		
		# Set quantity based on cancel flag
		if cancel:
			sle.actual_qty = abs(qty)  # Positive for cancellation
		else:
			sle.actual_qty = -abs(qty)  # Negative for sales
			
		sle.valuation_rate = rate
		sle.company = self.company
		# Get fiscal year from posting date
		try:
			from frappe.utils import get_fiscal_year
			fiscal_year = get_fiscal_year(self.posting_date, company=self.company)[0]
			sle.fiscal_year = fiscal_year
		except:
			# Fallback to current year if fiscal year calculation fails
			from frappe.utils import getdate
			sle.fiscal_year = str(getdate().year)
		
		sle.insert()
		sle.submit()
		
		# Update item standard rate only if not cancelling
		if not cancel:
			item_doc = frappe.get_doc("Item", item_code)
			item_doc.standard_rate = rate
			item_doc.save()

	def get_default_warehouse(self):
		"""Get default warehouse from Inventory Settings"""
		default_warehouse = frappe.db.get_single_value("Inventory Settings", "default_warehouse")
		if not default_warehouse:
			frappe.throw(_("Please set Default Warehouse in Inventory Settings"))
		return default_warehouse

	@frappe.whitelist()
	def process_payment(self, payment_details):
		"""Process payment and submit invoice"""
		# Clear existing payments
		self.payments = []
		
		# Add new payments
		for payment in payment_details:
			self.append("payments", {
				"payment_method": payment.get("payment_method"),
				"amount": flt(payment.get("amount"))
			})
		
		# Validate and save
		self.validate()
		self.save()
		
		# Submit if payment is sufficient
		if self.paid_amount >= self.grand_total:
			self.submit()
		
		return self

	@frappe.whitelist()
	def print_receipt(self):
		"""Generate receipt for printing"""
		return {
			"invoice": self.as_dict(),
			"items": [item.as_dict() for item in self.items],
			"payments": [payment.as_dict() for payment in self.payments],
			"company": frappe.get_doc("Company", self.company).as_dict(),
			"pos_profile": frappe.get_doc("POS Profile", self.pos_profile).as_dict()
		}

@frappe.whitelist()
def create_pos_invoice(pos_profile, items, customer="Walk-in Customer", payments=None, pos_session=None, pos_client=None):
	"""Create a new POS invoice"""
	import json
	
	# Parse JSON strings if needed
	if isinstance(items, str):
		items = json.loads(items)
	if isinstance(payments, str):
		payments = json.loads(payments)
	
	# Get POS profile data
	profile_doc = frappe.get_doc("POS Profile", pos_profile)
	
	# Use provided session or find open session
	if pos_session:
		# Validate the provided session
		session_data = frappe.db.get_value(
			"POS Session",
			pos_session,
			["status", "pos_profile", "pos_user"],
			as_dict=True
		)
		if not session_data:
			frappe.throw(_("Invalid POS session provided."))
		if session_data.status != "Open":
			frappe.throw(_("POS Session must be Open to create transactions."))
		if session_data.pos_user != frappe.session.user:
			frappe.throw(_("You can only create invoices for your own session."))
		session = pos_session
	else:
		# Get open session for current user
		session = frappe.db.get_value(
			"POS Session",
			{"pos_profile": pos_profile, "status": "Open", "pos_user": frappe.session.user},
			"name"
		)
		
		if not session:
			frappe.throw(_("No open POS session found. Please start a session first."))
	
	# Create invoice
	invoice = frappe.new_doc("POS Invoice")
	invoice.naming_series = "POS-INV-.YYYY.-.MM.-.DD.-.####"
	invoice.pos_profile = pos_profile
	invoice.pos_session = session
	invoice.customer = customer
	invoice.company = profile_doc.company_name or "Default Company"
	invoice.warehouse = profile_doc.warehouse_name
	invoice.currency = profile_doc.currency
	invoice.posting_date = getdate()
	invoice.posting_time = nowtime()
	
	# Add items
	for item_data in items:
		invoice.append("items", {
			"item_code": item_data.get("item_code"),
			"item_name": item_data.get("item_name"),
			"qty": flt(item_data.get("qty")),
			"rate": flt(item_data.get("rate")),
			"amount": flt(item_data.get("qty")) * flt(item_data.get("rate"))
		})
	
	# Add payments if provided
	if payments:
		for payment_data in payments:
			invoice.append("payments", {
				"payment_method": payment_data.get("payment_method"),
				"amount": flt(payment_data.get("amount"))
			})
	
	invoice.insert()
	invoice.submit()
	
	# Handle POS Client credit transaction if applicable
	if pos_client and payments:
		for payment in payments:
			if payment.get("payment_method") == "Credit":
				create_pos_client_transaction(
					pos_client,
					"Sale",
					flt(payment.get("amount")),
					invoice.name
				)
	
	return invoice

def create_pos_client_transaction(client_name, transaction_type, amount, reference_document=None):
	"""Create a POS Client Transaction record"""
	try:
		# Get current client balance
		client = frappe.get_doc("POS Client", client_name)
		
		# Calculate new balance
		if transaction_type == "Sale":
			new_balance = client.current_balance + amount
		elif transaction_type == "Payment":
			new_balance = client.current_balance - amount
		else:
			new_balance = client.current_balance
		
		# Create transaction record
		transaction = frappe.new_doc("POS Client Transaction")
		transaction.client = client_name
		transaction.transaction_type = transaction_type
		transaction.amount = amount
		transaction.balance_after = new_balance
		transaction.reference_document = reference_document
		transaction.insert()
		transaction.submit()
		
		# Update client balance
		frappe.db.set_value("POS Client", client_name, "current_balance", new_balance)
		frappe.db.commit()
		
		return transaction
		
	except Exception as e:
		frappe.log_error(f"Error creating POS client transaction: {str(e)}")
		frappe.throw(_("Error processing credit transaction: {0}").format(str(e)))