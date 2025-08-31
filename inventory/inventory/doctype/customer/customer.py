# Copyright (c) 2023, Your Name and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import cstr, strip_html

class Customer(Document):
    def validate(self):
        """Validate customer data"""
        self.validate_contact_number()
        self.validate_email()
        self.update_full_address()
    
    def validate_contact_number(self):
        """Ensure contact number is in valid format"""
        if self.contact_number:
            # Remove any non-digit characters except + at the beginning
            cleaned_number = ''.join([c for c in self.contact_number if c.isdigit() or (c == '+' and self.contact_number.index(c) == 0)])
            
            # Format the number properly
            if cleaned_number.startswith('+'):
                pass  # Keep international format
            elif cleaned_number.startswith('00'):
                cleaned_number = '+' + cleaned_number[2:]
            elif cleaned_number.startswith('0'):
                # Assume Algerian number if starts with 0
                cleaned_number = '+213' + cleaned_number[1:]
            
            self.contact_number = cleaned_number
    
    def validate_email(self):
        """Validate email format if provided"""
        if self.email:
            # Let Frappe handle email validation through the field's "Email" option
            pass
    

    
    def update_full_address(self):
        """Update the full address HTML display"""
        address_parts = []
        address_html = "<div class='address-display'>"
        
        if self.address:
            address_parts.append(self.address)
            address_html += f"<div>{self.address}</div>"
        
        commune_name = ""
        if self.commune:
            try:
                commune_name = frappe.get_value("Commune", self.commune, "commune_name") or self.commune
                address_parts.append(commune_name)
                address_html += f"<div>{commune_name}</div>"
            except:
                pass
        
        wilaya_name = ""
        if self.wilaya:
            try:
                wilaya_name = frappe.get_value("Wilaya", self.wilaya, "wilaya_name") or self.wilaya
                address_parts.append(wilaya_name)
                address_html += f"<div><strong>{wilaya_name}</strong></div>"
            except:
                pass
        
        # Close the HTML container
        address_html += "</div>"
        
        # Set both text and HTML versions of the address
        self.full_address = ", ".join(address_parts)
        self.full_address_display = address_html
    
    def on_update(self):
        """Actions to perform after customer is updated"""
        # Any actions needed on customer update
        pass
    
    def on_trash(self):
        """Actions to perform before customer is deleted"""
        # Check if there are dependent documents before allowing deletion
        sales_orders = frappe.get_all("Sales Order", filters={"customer": self.name}, limit=1)
        if sales_orders:
            frappe.throw("Cannot delete customer with linked Sales Orders. Please delete the Sales Orders first.")
        
        # Any other cleanup logic here
        pass 