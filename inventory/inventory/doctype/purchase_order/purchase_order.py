import frappe
from frappe.model.document import Document
from frappe.utils import getdate, now_datetime

class PurchaseOrder(Document):
    def validate(self):
        # Validate supplier
        if not self.supplier:
            frappe.throw("Supplier is required")
        
        # Validate items
        if not self.items:
            frappe.throw("At least one item is required")
        
        # Calculate total amount
        total_amount = 0
        for item in self.items:
            # Ensure amount is calculated
            if not item.amount:
                item.amount = item.quantity * item.rate
            total_amount += item.amount
        
        self.total_amount = total_amount
        
        # Validate dates
        if self.expected_delivery_date and getdate(self.order_date) > getdate(self.expected_delivery_date):
            frappe.throw("Expected Delivery Date cannot be before Order Date")
    
    def on_submit(self):
        # Update status
        self.status = "Ordered"
    
    def on_cancel(self):
        # Update status
        self.status = "Cancelled"
    
    def update_status(self, status):
        """
        Update the status of the Purchase Order
        """
        if status not in ["Draft", "Ordered", "Partially Received", "Completed", "Cancelled"]:
            frappe.throw("Invalid Status")
        
        self.status = status
        self.save()
        
    def create_purchase_receipt(self):
        """
        Create a Purchase Receipt from the Purchase Order
        """
        # Create Purchase Receipt
        pr = frappe.new_doc("Purchase Receipt")
        pr.supplier = self.supplier
        pr.receipt_date = now_datetime().date()
        pr.purchase_order = self.name
        
        # Add items from Purchase Order
        for item in self.items:
            pr.append("items", {
                "item": item.item,
                "quantity": item.quantity,
                "rate": item.rate,
                "amount": item.amount
            })
        
        pr.total_amount = self.total_amount
        
        return pr 