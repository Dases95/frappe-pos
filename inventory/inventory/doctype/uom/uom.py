import frappe
from frappe.model.document import Document

class UOM(Document):
    def validate(self):
        self.uom_name = self.uom_name.strip().title()
        self.uom_abbreviation = self.uom_abbreviation.strip().upper() 