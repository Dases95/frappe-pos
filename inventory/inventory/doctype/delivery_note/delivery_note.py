import frappe
from frappe.model.document import Document
from frappe.utils import getdate, now_datetime

class DeliveryNote(Document):
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
        
        # Check stock availability
        self.check_stock_availability()
    
    def check_stock_availability(self):
        """
        Check if stock is available for all items.
        Throws error if stock is insufficient to prevent submission.
        """
        # Get source warehouse from Inventory Settings
        try:
            source_warehouse = frappe.db.get_single_value("Inventory Settings", "default_warehouse")
            if not source_warehouse:
                frappe.throw("Default Warehouse not set in Inventory Settings. Cannot validate stock availability.")
        except frappe.DoesNotExistError:
            frappe.throw("Inventory Settings doctype not found. Please create it first.")
        
        insufficient_items = []
        
        for item in self.items:
            # Get available stock from the source warehouse
            available_stock = frappe.db.sql("""
                SELECT COALESCE(SUM(actual_qty), 0) 
                FROM `tabStock Ledger Entry` 
                WHERE item = %s 
                AND warehouse = %s 
                AND is_cancelled = 0
            """, (item.item, source_warehouse))[0][0] or 0
            
            if available_stock < item.quantity:
                insufficient_items.append({
                    "item": item.item,
                    "item_name": item.item_name or item.item,
                    "available": available_stock,
                    "required": item.quantity,
                    "shortage": item.quantity - available_stock
                })
        
        # If any items have insufficient stock, throw error
        if insufficient_items:
            error_messages = []
            for item_info in insufficient_items:
                error_messages.append(
                    f"<li><b>{item_info['item_name']}</b> ({item_info['item']}): "
                    f"Available: {item_info['available']}, Required: {item_info['required']}, "
                    f"Shortage: {item_info['shortage']}</li>"
                )
            
            frappe.throw(
                f"Insufficient stock in warehouse <b>{source_warehouse}</b> for the following items:<br><ul>{''.join(error_messages)}</ul>"
                f"<br>Please check stock availability before creating this Delivery Note.",
                title="Insufficient Stock"
            )
    
    def on_submit(self):
        # Create Stock Entry
        self.create_stock_entry()
        
        # Update Sales Order status if linked
        if self.sales_order:
            self.update_sales_order_status()
    
    def on_cancel(self):
        # Update Sales Order status if linked
        if self.sales_order:
            self.update_sales_order_status(cancelled=True)
    
    def create_stock_entry(self):
        """
        Create a Stock Entry for delivered items
        
        Note: We use "Sale" entry type for delivery notes to track sales separately
        from internal "Issue" movements
        """
        stock_entry = frappe.new_doc("Stock Entry")
        stock_entry.entry_type = "Sale"  # Sale type for customer deliveries
        stock_entry.reference_document = self.name
        stock_entry.date = self.delivery_date
        
        # Get source warehouse from Inventory Settings
        try:
            source_warehouse = frappe.db.get_single_value("Inventory Settings", "default_warehouse")
            if not source_warehouse:
                frappe.throw("Default Warehouse not set in Inventory Settings")
            stock_entry.source_warehouse = source_warehouse
        except frappe.DoesNotExistError:
            frappe.throw("Inventory Settings doctype not found. Please create it first.")
        
        for item in self.items:
            # Include rate and amount for proper valuation
            item_rate = frappe.db.get_value("Item", item.item, "valuation_rate") if not item.rate else item.rate
            item_amount = item.quantity * item_rate
            
            stock_entry.append("items", {
                "item": item.item,
                "quantity": item.quantity,
                "batch": item.batch,
                "rate": item_rate,  # Added rate for proper valuation
                "amount": item_amount  # Added amount for proper valuation
            })
        
        stock_entry.insert()
        stock_entry.submit()
        
        frappe.msgprint("Stock Entry created")
    
    def update_sales_order_status(self, cancelled=False):
        """
        Update the status of the linked Sales Order
        """
        if not cancelled:
            # Get the Sales Order
            so = frappe.get_doc("Sales Order", self.sales_order)
            
            # Check if all items are delivered
            all_delivered = True
            
            # Get all delivery notes against this SO
            delivery_notes = frappe.get_all(
                "Delivery Note",
                filters={"sales_order": self.sales_order, "docstatus": 1},
                fields=["name"]
            )
            
            # Get all items in delivery notes
            delivered_items = {}
            for dn in delivery_notes:
                dn_items = frappe.get_all(
                    "Delivery Note Item",
                    filters={"parent": dn.name, "sales_order": self.sales_order},
                    fields=["item", "quantity"]
                )
                
                for item in dn_items:
                    if item.item in delivered_items:
                        delivered_items[item.item] += item.quantity
                    else:
                        delivered_items[item.item] = item.quantity
            
            # Compare with SO items
            so_items = frappe.get_all(
                "Sales Order Item",
                filters={"parent": self.sales_order},
                fields=["item", "quantity"]
            )
            
            for item in so_items:
                delivered_qty = delivered_items.get(item.item, 0)
                if delivered_qty < item.quantity:
                    all_delivered = False
                    break
            
            # Update status
            if all_delivered:
                so.update_status("Completed")
            else:
                so.update_status("Partially Delivered")
        else:
            # Cancelled case - recheck status
            so = frappe.get_doc("Sales Order", self.sales_order)
            
            # Get all active delivery notes against this SO
            delivery_notes = frappe.get_all(
                "Delivery Note",
                filters={"sales_order": self.sales_order, "docstatus": 1},
                fields=["name"]
            )
            
            if not delivery_notes:
                so.update_status("Ordered")
            else:
                so.update_status("Partially Delivered") 