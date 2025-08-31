import frappe
from frappe.model.document import Document
from frappe.utils import getdate, date_diff, nowdate

class Batch(Document):
    def validate(self):
        # Ensure batch ID is unique
        if frappe.db.exists("Batch", {"batch_id": self.batch_id, "name": ["!=", self.name]}):
            frappe.throw("Batch ID already exists!")
        
        # Validate manufacturing and expiry dates
        if self.manufacturing_date and self.expiry_date:
            if getdate(self.manufacturing_date) > getdate(self.expiry_date):
                frappe.throw("Manufacturing Date cannot be after Expiry Date")
        
        # Check if batch has expired
        if self.expiry_date and getdate(self.expiry_date) < getdate(nowdate()):
            self.has_expired = 1
        else:
            self.has_expired = 0 