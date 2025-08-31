import frappe
from frappe.model.document import Document
from frappe.utils import getdate, now_datetime

class SalesOrder(Document):
    def validate(self):
        # Validate customer
        if not self.customer:
            frappe.throw("Customer is required")
        
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
        
        # Check stock availability
        self.check_stock_availability()
    
    def check_stock_availability(self):
        """
        Check if stock is available for all items
        """
        for item in self.items:
            # Get available stock from all warehouses
            available_stock = frappe.db.sql("""
                SELECT SUM(actual_qty) 
                FROM `tabStock Ledger Entry` 
                WHERE item = %s AND is_cancelled = 0
            """, item.item)[0][0] or 0
            
            if available_stock < item.quantity:
                frappe.msgprint(f"Insufficient stock for item {item.item_name} ({item.item}). Available: {available_stock}, Required: {item.quantity}")
    
    def on_submit(self):
        # Update status
        self.status = "Ordered"
    
    def on_cancel(self):
        # Update status
        self.status = "Cancelled"
    
    def update_status(self, status):
        """
        Update the status of the Sales Order
        """
        if status not in ["Draft", "Ordered", "Partially Delivered", "Completed", "Cancelled"]:
            frappe.throw("Invalid Status")
        
        self.status = status
        self.save()
        
    def create_delivery_note(self):
        """
        Create a Delivery Note from the Sales Order
        """
        # Create Delivery Note
        dn = frappe.new_doc("Delivery Note")
        dn.customer = self.customer
        dn.delivery_date = now_datetime().date()
        dn.sales_order = self.name
        
        # Add items from Sales Order
        for item in self.items:
            dn.append("items", {
                "item": item.item,
                "quantity": item.quantity,
                "rate": item.rate,
                "amount": item.amount
            })
        
        dn.total_amount = self.total_amount
        
        return dn 