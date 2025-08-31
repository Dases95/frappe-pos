import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, flt

class StockEntry(Document):
    def validate(self):
        # Validate entry type and warehouses
        if self.entry_type == "Receipt":
            if not self.target_warehouse:
                frappe.throw("Target Warehouse is required for Receipt entry")
        elif self.entry_type == "Issue":
            if not self.source_warehouse:
                frappe.throw("Source Warehouse is required for Issue entry")
        elif self.entry_type == "Transfer":
            if not self.source_warehouse or not self.target_warehouse:
                frappe.throw("Both Source and Target Warehouses are required for Transfer entry")
            if self.source_warehouse == self.target_warehouse:
                frappe.throw("Source and Target Warehouses cannot be the same for Transfer")
        elif self.entry_type == "Manufacture":
            if not self.target_warehouse:
                frappe.throw("Target Warehouse is required for Manufacture entry")
        
        # Validate items
        if not self.items:
            frappe.throw("At least one item is required")
        
        # Set posting date to current date if not provided
        if not self.date:
            self.date = now_datetime().date()
            
        # Calculate amounts for each item
        self.calculate_totals()
    
    def calculate_totals(self):
        total_amount = 0
        for item in self.items:
            if item.quantity and item.rate:
                item.amount = flt(item.quantity) * flt(item.rate)
            else:
                item.amount = 0
                
            total_amount += flt(item.amount)
            
        self.total_amount = total_amount
    
    def on_submit(self):
        # Create stock ledger entries
        self.update_stock_ledger()
        
        # Update item valuation rates
        self.update_item_valuation_rates()
    
    def on_cancel(self):
        # Revert stock ledger entries
        self.update_stock_ledger(is_cancelled=True)
    
    def update_item_valuation_rates(self):
        # Only update valuation rates for receipt entries
        if self.entry_type in ["Receipt", "Manufacture"]:
            for item_row in self.items:
                if not item_row.rate:
                    continue
                    
                # For receipt entries, update valuation rate with weighted average
                # Get current stock information
                stock_data = frappe.db.sql("""
                    SELECT 
                        SUM(actual_qty) as qty,
                        SUM(actual_qty * valuation_rate) as value
                    FROM 
                        `tabStock Ledger Entry`
                    WHERE 
                        item = %s 
                        AND warehouse = %s
                        AND is_cancelled = 0
                """, (item_row.item, self.target_warehouse), as_dict=1)
                
                current_qty = flt(stock_data[0].qty) if stock_data and stock_data[0].qty else 0
                current_value = flt(stock_data[0].value) if stock_data and stock_data[0].value else 0
                
                if current_qty > 0:
                    # Calculate weighted average valuation rate
                    new_valuation_rate = current_value / current_qty
                    
                    # Update item's valuation rate
                    frappe.db.set_value("Item", item_row.item, "valuation_rate", new_valuation_rate)
                    
                    # For purchase receipts, update last purchase rate as well
                    if self.entry_type == "Receipt":
                        frappe.db.set_value("Item", item_row.item, "last_purchase_rate", item_row.rate)
    
    def update_stock_ledger(self, is_cancelled=False):
        for item in self.items:
            # Handle stock updates based on entry type
            if self.entry_type == "Receipt":
                self.create_stock_ledger_entry(
                    item.item,
                    self.target_warehouse,
                    item.quantity,
                    "in",
                    item.batch,
                    item.rate,
                    is_cancelled
                )
            elif self.entry_type == "Issue":
                self.create_stock_ledger_entry(
                    item.item,
                    self.source_warehouse,
                    item.quantity,
                    "out",
                    item.batch,
                    item.rate,
                    is_cancelled
                )
            elif self.entry_type == "Transfer":
                # Deduct from source warehouse
                self.create_stock_ledger_entry(
                    item.item,
                    self.source_warehouse,
                    item.quantity,
                    "out",
                    item.batch,
                    item.rate,
                    is_cancelled
                )
                # Add to target warehouse
                self.create_stock_ledger_entry(
                    item.item,
                    self.target_warehouse,
                    item.quantity,
                    "in",
                    item.batch,
                    item.rate,
                    is_cancelled
                )
            elif self.entry_type == "Manufacture":
                self.create_stock_ledger_entry(
                    item.item,
                    self.target_warehouse,
                    item.quantity,
                    "in",
                    item.batch,
                    item.rate,
                    is_cancelled
                )
    
    def create_stock_ledger_entry(self, item_code, warehouse, qty, qty_type, batch=None, rate=0, is_cancelled=False):
        # Adjust quantity based on entry type and cancellation status
        actual_qty = qty
        if qty_type == "out" or is_cancelled:
            actual_qty = -1 * qty
            if is_cancelled and qty_type == "out":
                actual_qty = qty  # Double negative becomes positive
        elif is_cancelled and qty_type == "in":
            actual_qty = -1 * qty
        
        # Calculate stock value difference
        stock_value_difference = flt(actual_qty) * flt(rate)
        
        # If it's an outward entry, get the current valuation rate
        if not rate and qty_type == "out":
            rate = frappe.db.get_value("Item", item_code, "valuation_rate") or 0
        
        # Create Stock Ledger Entry
        sle = frappe.new_doc("Stock Ledger Entry")
        sle.item = item_code
        sle.warehouse = warehouse
        sle.posting_date = self.date
        sle.posting_time = now_datetime().time()
        sle.voucher_type = "Stock Entry"
        sle.voucher_no = self.name
        sle.voucher_detail_no = ""
        sle.actual_qty = actual_qty
        sle.batch_no = batch
        sle.valuation_rate = rate
        sle.stock_value_difference = stock_value_difference
        sle.company = "hjjhhj"#frappe.defaults.get_global_default('company')
        sle.fiscal_year = "2025"#frappe.defaults.get_global_default('fiscal_year')
        sle.is_cancelled = is_cancelled
        sle.insert()