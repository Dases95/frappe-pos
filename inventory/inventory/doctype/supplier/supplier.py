import frappe
from frappe.model.document import Document

class Supplier(Document):
    def validate(self):
        # Validate email format if provided
        if self.email and not frappe.utils.validate_email_address(self.email):
            frappe.throw("Invalid Email Format") 