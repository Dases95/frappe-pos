import frappe
from frappe.model.document import Document
from frappe.utils import flt
from frappe import _

class StockLedgerEntry(Document):
	def validate(self):
		"""Validate stock ledger entry"""
		self.validate_mandatory_fields()
		self.validate_item_and_warehouse()
	
	def validate_mandatory_fields(self):
		"""Validate that all required fields are present"""
		if not self.item:
			frappe.throw(_("Item is required"))
		if not self.warehouse:
			frappe.throw(_("Warehouse is required"))
		if not self.posting_date:
			frappe.throw(_("Posting Date is required"))
		if not self.voucher_type:
			frappe.throw(_("Voucher Type is required"))
		if not self.voucher_no:
			frappe.throw(_("Voucher No is required"))
	
	def validate_item_and_warehouse(self):
		"""Validate that item and warehouse exist"""
		if not frappe.db.exists("Item", self.item):
			frappe.throw(_("Item {0} does not exist").format(self.item))
		if not frappe.db.exists("Warehouse", self.warehouse):
			frappe.throw(_("Warehouse {0} does not exist").format(self.warehouse))
	
	def on_submit(self):
		"""Update stock balance after submission"""
		self.update_stock_balance()
	
	def on_cancel(self):
		"""Reverse stock balance on cancellation"""
		self.update_stock_balance(reverse=True)
	
	def update_stock_balance(self, reverse=False):
		"""Update the stock balance for the item in the warehouse"""
		try:
			# Calculate the quantity change
			qty_change = flt(self.actual_qty)
			if reverse:
				qty_change = -1 * qty_change
			
			# Get current stock balance
			current_balance = self.get_current_stock_balance()
			new_balance = current_balance + qty_change
			
			# Update or create stock balance record
			self.update_stock_balance_record(new_balance)
			
			frappe.db.commit()
			
		except Exception as e:
			frappe.log_error(f"Error updating stock balance: {str(e)}", "Stock Balance Update Error")
			frappe.throw(_("Failed to update stock balance: {0}").format(str(e)))
	
	def get_current_stock_balance(self):
		"""Get current stock balance for item in warehouse from Stock Ledger Entry"""
		# Calculate current balance from all stock ledger entries
		balance = frappe.db.sql("""
			SELECT COALESCE(SUM(actual_qty), 0) as balance
			FROM `tabStock Ledger Entry`
			WHERE item = %s AND warehouse = %s
			AND name != %s
		""", (self.item, self.warehouse, self.name or ''), as_dict=True)[0].balance
		return flt(balance)
	
	def update_stock_balance_record(self, new_balance):
		"""Stock balance is now calculated dynamically from Stock Ledger Entry records"""
		# No need to maintain separate stock balance records
		# Stock balance is calculated on-demand from Stock Ledger Entry
		pass