import frappe
from frappe.model.document import Document

class PriceList(Document):
    def validate(self):
        # Validate at least one of buying or selling is checked
        if not (self.buying or self.selling):
            frappe.throw("Price List must be designated for either buying or selling.")
            
        # Set currency to uppercase
        if self.currency:
            self.currency = self.currency.upper() 