import frappe
from frappe.model.document import Document
from frappe.utils import getdate, now_datetime

class ManufacturingOrder(Document):
    def validate(self):
        # Validate finished item
        if not self.item_to_manufacture:
            frappe.throw("Item to Manufacture is required")
        
        # Validate quantity
        if self.quantity <= 0:
            frappe.throw("Quantity must be greater than zero")
        
        # Validate BOM reference
        if not self.bom_reference:
            frappe.throw("BOM Reference is required")
        
        # Validate target warehouse
        if not self.target_warehouse:
            frappe.throw("Target Warehouse is required")
        
        # Validate dates
        if self.planned_end_date and getdate(self.planned_start_date) > getdate(self.planned_end_date):
            frappe.throw("Planned End Date cannot be before Planned Start Date")
    
    def on_submit(self):
        # Update status
        self.status = "In Process"
    
    def on_cancel(self):
        # Update status
        self.status = "Cancelled"
    
    def update_status(self, status):
        """
        Update the status of the Manufacturing Order
        """
        if status not in ["Draft", "In Process", "Completed", "Cancelled"]:
            frappe.throw("Invalid Status")
        
        self.status = status
        self.save()
    
    def start_production(self):
        """
        Start the production process by issuing raw materials
        """
        if self.status != "In Process":
            frappe.throw("Manufacturing Order must be in 'In Process' status to start production")
        
        # Get BOM details
        bom = frappe.get_doc("BOM", self.bom_reference)
        
        # Create Stock Entry for raw material consumption
        stock_entry = frappe.new_doc("Stock Entry")
        stock_entry.entry_type = "Issue"
        stock_entry.reference_document = self.name
        stock_entry.date = now_datetime().date()
        
        # Get source warehouse from settings or use a default
        source_warehouse = frappe.db.get_single_value("Inventory Settings", "default_warehouse")
        stock_entry.source_warehouse = source_warehouse
        
        # Add raw materials from BOM
        for item in bom.raw_materials:
            # Calculate required quantity based on manufacturing quantity
            required_qty = item.quantity * self.quantity / bom.quantity
            
            stock_entry.append("items", {
                "item": item.item,
                "quantity": required_qty
            })
        
        stock_entry.insert()
        stock_entry.submit()
        
        frappe.msgprint("Raw materials issued for production")
    
    def complete_production(self):
        """
        Complete the production process by receiving finished goods
        """
        if self.status != "In Process":
            frappe.throw("Manufacturing Order must be in 'In Process' status to complete production")
        
        # Create Stock Entry for finished goods
        stock_entry = frappe.new_doc("Stock Entry")
        stock_entry.entry_type = "Receipt"
        stock_entry.reference_document = self.name
        stock_entry.date = now_datetime().date()
        stock_entry.target_warehouse = self.target_warehouse
        
        # Add finished item
        stock_entry.append("items", {
            "item": self.item_to_manufacture,
            "quantity": self.quantity
        })
        
        stock_entry.insert()
        stock_entry.submit()
        
        # Update status
        self.actual_end_date = now_datetime().date()
        self.update_status("Completed")
        
        frappe.msgprint("Production completed, finished goods received") 