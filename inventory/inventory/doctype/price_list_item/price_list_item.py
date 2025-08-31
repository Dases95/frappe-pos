import frappe
from frappe.model.document import Document

class PriceListItem(Document):
    def validate(self):
        # Validate rate is positive
        if self.rate <= 0:
            frappe.throw("Rate must be greater than zero") 