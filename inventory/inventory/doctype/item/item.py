import frappe
from frappe.model.document import Document

class Item(Document):
    def validate(self):
        # Validate item code uniqueness
        if frappe.db.exists("Item", {"item_code": self.item_code, "name": ["!=", self.name]}):
            frappe.throw("Item Code already exists!")
        
        # Validate reorder levels
        if self.reorder_level and self.minimum_stock_level:
            if self.reorder_level < self.minimum_stock_level:
                frappe.throw("Reorder Level cannot be less than Minimum Stock Level!") 