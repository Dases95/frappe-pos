# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now, getdate, flt, now_datetime


class POSSession(Document):
	def validate(self):
		self.validate_session_status()
		self.validate_opening_time()
		self.set_status()

	def before_save(self):
		if self.status == "Open":
			self.update_session_totals()

	def validate_session_status(self):
		if self.status == "Closed":
			frappe.throw(_("Cannot modify a closed session"))

	def validate_opening_time(self):
		if not self.opening_time and self.status in ["Open", "Closing"]:
			self.opening_time = now()

	def set_status(self):
		if self.status == "Opening" and self.opening_time:
			self.status = "Open"

	def update_session_totals(self):
		"""Update session totals from POS Invoices including profit analysis"""
		invoices = frappe.get_all(
			"POS Invoice",
			filters={
				"pos_session": self.name,
				"docstatus": 1
			},
			fields=["net_total", "grand_total", "total_qty", "total_cost", "total_profit"]
		)
		
		self.net_total = sum(flt(inv.net_total) for inv in invoices)
		self.grand_total = sum(flt(inv.grand_total) for inv in invoices)
		self.total_quantity = sum(flt(inv.total_qty) for inv in invoices)
		self.total_cost = sum(flt(inv.total_cost) for inv in invoices)
		self.total_profit = sum(flt(inv.total_profit) for inv in invoices)
		
		# Calculate overall profit margin for the session
		if self.net_total > 0:
			self.profit_margin_percent = (self.total_profit / self.net_total) * 100
		else:
			self.profit_margin_percent = 0
		
		self.closing_amount = flt(self.opening_amount) + self.net_total

	def update_payment_reconciliation(self):
		"""Update payment reconciliation details"""
		# Clear existing reconciliation
		self.payment_reconciliation_details = []
		
		# Get all payment methods used in this session
		payment_data = frappe.db.sql("""
			SELECT 
				ip.payment_method,
				SUM(ip.amount) as total_amount,
				COUNT(ip.name) as transaction_count
			FROM `tabPOS Invoice Payment` ip
			JOIN `tabPOS Invoice` pi ON ip.parent = pi.name
			WHERE pi.pos_session = %s AND pi.docstatus = 1
			GROUP BY ip.payment_method
		""", self.name, as_dict=True)
		
		for payment in payment_data:
			self.append("payment_reconciliation_details", {
				"payment_method": payment.payment_method,
				"expected_amount": payment.total_amount,
				"actual_amount": payment.total_amount,  # TODO: Allow manual entry
				"difference": 0
			})

	@frappe.whitelist()
	def close_session(self, closing_amount=None):
		"""Close the POS session"""
		if self.status == "Closed":
			frappe.throw(_("Session is already closed"))
		
		self.update_session_totals()
		self.status = "Closing"
		self.closing_time = now()
		self.period_end_date = getdate()
		
		if closing_amount:
			self.closing_amount = flt(closing_amount)
		
		self.update_payment_reconciliation()
		self.status = "Closed"
		self.save()
		
		return self

	@frappe.whitelist()
	def get_session_summary(self):
		"""Get session summary for the POS interface including profit analysis"""
		return {
			"session": self.as_dict(),
			"total_sales": self.grand_total,
			"total_qty": self.total_quantity,
			"total_cost": self.total_cost,
			"total_profit": self.total_profit,
			"profit_margin_percent": self.profit_margin_percent,
			"payment_summary": [p.as_dict() for p in self.payment_reconciliation_details]
		}


@frappe.whitelist()
def create_opening_entry(pos_profile, opening_amount=0):
	"""Create a new POS session opening entry"""
	# Check if there's already an open session for this profile
	existing_session = frappe.db.get_value(
		"POS Session",
		{
			"pos_profile": pos_profile,
			"status": ["in", ["Opening", "Open"]],
			"user": frappe.session.user
		},
		"name"
	)
	
	if existing_session:
		session_doc = frappe.get_doc("POS Session", existing_session)
		# Get warehouse from POS Profile
		profile_doc = frappe.get_doc("POS Profile", pos_profile)
		session_dict = session_doc.as_dict()
		session_dict['warehouse'] = profile_doc.warehouse_name
		return session_dict
	
	# Create new session
	session = frappe.new_doc("POS Session")
	session.pos_profile = pos_profile
	session.user = frappe.session.user
	session.period_start_date = getdate()
	session.opening_amount = flt(opening_amount)
	session.status = "Opening"
	session.insert()
	
	# Get warehouse from POS Profile and add to response
	profile_doc = frappe.get_doc("POS Profile", pos_profile)
	session_dict = session.as_dict()
	session_dict['warehouse'] = profile_doc.warehouse_name
	return session_dict


@frappe.whitelist()
def close_session(session_name):
	"""Close a POS session"""
	session = frappe.get_doc("POS Session", session_name)
	return session.close_session()


@frappe.whitelist()
def get_open_session():
	"""Get the current open session for the user"""
	return frappe.db.get_value(
		"POS Session",
		{
			"user": frappe.session.user,
			"status": ["in", ["Opening", "Open"]]
		},
		"name"
	)