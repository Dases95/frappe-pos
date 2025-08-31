import frappe
from frappe.model.document import Document

class StockEntryItem(Document):
    def validate(self):
        # Validate quantity is positive
        if self.quantity <= 0:
            frappe.throw("Quantity must be greater than zero") 