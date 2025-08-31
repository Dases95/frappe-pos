import frappe
from frappe.model.document import Document

class SalesOrderItem(Document):
    def validate(self):
        # Validate quantity and rate are positive
        if self.quantity <= 0:
            frappe.throw("Quantity must be greater than zero")
        
        if self.rate <= 0:
            frappe.throw("Rate must be greater than zero")
        
        # Calculate amount
        self.amount = self.quantity * self.rate 