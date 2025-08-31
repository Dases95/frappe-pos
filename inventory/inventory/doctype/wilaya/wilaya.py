# Copyright (c) 2023, Your Name and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Wilaya(Document):
    def validate(self):
        # Ensure wilaya_code is numeric
        if self.wilaya_code and not self.wilaya_code.isdigit():
            frappe.throw("Wilaya Code must be numeric") 