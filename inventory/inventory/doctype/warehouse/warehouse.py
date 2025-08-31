import frappe
from frappe.model.document import Document

class Warehouse(Document):
    def validate(self):
        # Validate warehouse code uniqueness
        if frappe.db.exists("Warehouse", {"warehouse_code": self.warehouse_code, "name": ["!=", self.name]}):
            frappe.throw("Warehouse Code already exists!") 