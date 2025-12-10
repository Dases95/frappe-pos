import frappe
from frappe.model.document import Document
from frappe.utils import getdate, now_datetime

class PurchaseReceipt(Document):
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
    
    def on_submit(self):
        # Create Stock Entry
        self.create_stock_entry()
        
        # Update Purchase Order status if linked
        if self.purchase_order:
            self.update_purchase_order_status()
        
        # Update Item Last Purchase Rate
        self.update_item_rates()
    
    def on_cancel(self):
        # Update Purchase Order status if linked
        if self.purchase_order:
            self.update_purchase_order_status(cancelled=True)
    
    def update_item_rates(self):
        """
        Update the last purchase rate in Item
        """
        for item in self.items:
            if item.rate:
                frappe.db.set_value("Item", item.item, "last_purchase_rate", item.rate)
    
    def create_stock_entry(self):
        """
        Create a Stock Entry for received items from suppliers
        
        Note: We use "Purchase" entry type to track supplier purchases separately
        from internal "Receipt" movements
        """
        stock_entry = frappe.new_doc("Stock Entry")
        stock_entry.entry_type = "Purchase"  # Purchase type for supplier receipts
        stock_entry.reference_document = self.name
        stock_entry.date = self.receipt_date
        
        # Try to get default warehouse from Inventory Settings
        try:
            default_warehouse = frappe.db.get_single_value("Inventory Settings", "default_warehouse")
            if not default_warehouse:
                frappe.throw("Default Warehouse not set in Inventory Settings")
            stock_entry.target_warehouse = default_warehouse
        except frappe.DoesNotExistError:
            frappe.throw("Inventory Settings doctype not found. Please create it first.")
        
        for item in self.items:
            stock_entry.append("items", {
                "item": item.item,
                "quantity": item.quantity,
                "batch": item.batch,
                "rate": item.rate,
                "amount": item.amount
            })
        
        stock_entry.insert()
        stock_entry.submit()
        
        frappe.msgprint("Stock Entry created")
    
    def update_purchase_order_status(self, cancelled=False):
        """
        Update the status of the linked Purchase Order
        """
        if not cancelled:
            # Get the Purchase Order
            po = frappe.get_doc("Purchase Order", self.purchase_order)
            
            # Check if all items are received
            all_received = True
            
            # Get all purchase receipts against this PO
            purchase_receipts = frappe.get_all(
                "Purchase Receipt",
                filters={"purchase_order": self.purchase_order, "docstatus": 1},
                fields=["name"]
            )
            
            # Get all items in purchase receipts
            receipt_items = {}
            for pr in purchase_receipts:
                pr_items = frappe.get_all(
                    "Purchase Receipt Item",
                    filters={"parent": pr.name, "purchase_order": self.purchase_order},
                    fields=["item", "quantity"]
                )
                
                for item in pr_items:
                    if item.item in receipt_items:
                        receipt_items[item.item] += item.quantity
                    else:
                        receipt_items[item.item] = item.quantity
            
            # Compare with PO items
            po_items = frappe.get_all(
                "Purchase Order Item",
                filters={"parent": self.purchase_order},
                fields=["item", "quantity"]
            )
            
            for item in po_items:
                received_qty = receipt_items.get(item.item, 0)
                if received_qty < item.quantity:
                    all_received = False
                    break
            
            # Update status
            if all_received:
                po.update_status("Completed")
            else:
                po.update_status("Partially Received")
        else:
            # Cancelled case - recheck status
            po = frappe.get_doc("Purchase Order", self.purchase_order)
            
            # Get all active purchase receipts against this PO
            purchase_receipts = frappe.get_all(
                "Purchase Receipt",
                filters={"purchase_order": self.purchase_order, "docstatus": 1},
                fields=["name"]
            )
            
            if not purchase_receipts:
                po.update_status("Ordered")
            else:
                po.update_status("Partially Received") 