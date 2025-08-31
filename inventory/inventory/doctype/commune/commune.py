# Copyright (c) 2023, Your Name and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Commune(Document):
    def validate(self):
        # Ensure commune_code is numeric
        if self.commune_code and not self.commune_code.isdigit():
            frappe.throw("Commune Code must be numeric") 