# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate, nowdate
from inventory.pos.doctype.pos_profile.pos_profile import get_default_pos_profile


@frappe.whitelist()
def get_pos_invoices_for_modification(limit=20):
    """Get recent POS invoices that can be modified"""
    try:
        # Get recent invoices from current user's sessions
        invoices = frappe.db.sql("""
            SELECT 
                pi.name,
                pi.posting_date,
                pi.posting_time,
                pi.customer,
                pi.grand_total,
                pi.status,
                pi.pos_session,
                ps.pos_profile
            FROM "tabPOS Invoice" pi
            LEFT JOIN "tabPOS Session" ps ON pi.pos_session = ps.name
            WHERE pi.docstatus = 1
                AND ps.pos_user = %s
                AND pi.posting_date >= CURRENT_DATE - INTERVAL '7 days'
            ORDER BY pi.creation DESC
            LIMIT %s
        """, (frappe.session.user, limit), as_dict=True)
        
        return invoices
        
    except Exception as e:
        frappe.log_error(f"Error in get_pos_invoices_for_modification: {str(e)}")
        return []


@frappe.whitelist()
def get_pos_invoice_details(invoice_name):
    """Get detailed invoice data for modification"""
    try:
        # Get invoice document
        invoice = frappe.get_doc("POS Invoice", invoice_name)
        
        # Check if user has permission to modify this invoice
        session = frappe.get_doc("POS Session", invoice.pos_session)
        if session.pos_user != frappe.session.user:
            frappe.throw(_("You don't have permission to modify this invoice"))
        
        # Get invoice items
        items = []
        for item in invoice.items:
            items.append({
                "item_code": item.item_code,
                "item_name": item.item_name,
                "qty": item.qty,
                "rate": item.rate,
                "amount": item.amount
            })
        
        # Get payments
        payments = []
        for payment in invoice.payments:
            payments.append({
                "payment_method": payment.payment_method,
                "amount": payment.amount
            })
        
        return {
            "invoice": {
                "name": invoice.name,
                "customer": invoice.customer,
                "posting_date": invoice.posting_date,
                "posting_time": invoice.posting_time,
                "grand_total": invoice.grand_total,
                "pos_session": invoice.pos_session,
                "pos_profile": invoice.pos_profile
            },
            "items": items,
            "payments": payments
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_pos_invoice_details: {str(e)}")
        frappe.throw(_("Error loading invoice details: {0}").format(str(e)))


@frappe.whitelist()
def update_pos_invoice(invoice_name, items, payments, customer="Walk-in Customer"):
    """Update an existing POS invoice"""
    import json
    
    try:
        # Parse JSON strings if needed
        if isinstance(items, str):
            items = json.loads(items)
        if isinstance(payments, str):
            payments = json.loads(payments)
        
        # Get and validate invoice
        invoice = frappe.get_doc("POS Invoice", invoice_name)
        
        # Check permissions
        session = frappe.get_doc("POS Session", invoice.pos_session)
        if session.user != frappe.session.user:
            frappe.throw(_("You don't have permission to modify this invoice"))
        
        # Cancel the original invoice
        invoice.cancel()
        
        # Create a new invoice with updated data
        new_invoice = frappe.new_doc("POS Invoice")
        new_invoice.pos_profile = invoice.pos_profile
        new_invoice.pos_session = invoice.pos_session
        new_invoice.customer = customer
        new_invoice.posting_date = invoice.posting_date
        new_invoice.posting_time = invoice.posting_time
        new_invoice.company = invoice.company
        new_invoice.currency = invoice.currency
        
        # Add items
        for item_data in items:
            new_invoice.append("items", {
                "item_code": item_data["item_code"],
                "qty": item_data["qty"],
                "rate": item_data["rate"]
            })
        
        # Add payments
        for payment_data in payments:
            new_invoice.append("payments", {
                "payment_method": payment_data["payment_method"],
                "amount": payment_data["amount"]
            })
        
        # Save and submit
        new_invoice.save()
        new_invoice.submit()
        
        return {
            "success": True,
            "message": _("Invoice updated successfully"),
            "new_invoice": new_invoice.name,
            "cancelled_invoice": invoice_name
        }
        
    except Exception as e:
        frappe.log_error(f"Error in update_pos_invoice: {str(e)}")
        frappe.throw(_("Error updating invoice: {0}").format(str(e)))


@frappe.whitelist()
def get_pos_data():
    """Get all data needed for POS interface"""
    try:
        # Get current user's default POS profile
        pos_profile = get_user_pos_profile()

        if not pos_profile:
            return {"error": "No POS Profile assigned to current user"}
        
        # Get open session
        open_session = get_current_open_session()
        
        # Get items with stock data
        items = get_pos_items(pos_profile.warehouse if pos_profile else None)
        
        # Get payment methods
        payment_methods = pos_profile.payment_methods if pos_profile else []
        
        return {
            "pos_profile": pos_profile.as_dict() if pos_profile else None,
            "open_session": open_session.as_dict() if open_session else None,
            "items": items,
            "payment_methods": [pm.as_dict() for pm in payment_methods]
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_pos_data: {str(e)}")
        return {"error": str(e)}


def get_user_pos_profile():
    """Get POS profile for current user"""
    # Check if user has a specific POS profile assigned
    pos_profile_name = frappe.db.get_value(
        "POS Profile User",
        {"user": frappe.session.user},
        "parent"
    )
    
    if not pos_profile_name:
        # Get default POS profile
        pos_profile_name = frappe.db.get_value(
            "POS Profile",
            {"is_default": 1},
            "name"
        )
    
    if pos_profile_name:
        return frappe.get_doc("POS Profile", pos_profile_name)
    
    return None


def get_current_open_session():
    """Get current open POS session for user"""
    session_name = frappe.db.get_value(
        "POS Session",
        {
            "pos_user": frappe.session.user,
            "status": ["in", ["Opening", "Open"]]
        },
        "name"
    )
    
    if session_name:
        return frappe.get_doc("POS Session", session_name)
    
    return None


@frappe.whitelist()
def get_pos_items(warehouse=None, search_term=""):
    """Get items available for POS with stock information"""

    try:
        # If no warehouse is provided, get it from the default POS profile
        if not warehouse:
            default_profile = get_default_pos_profile()
            if default_profile and default_profile.warehouse_name:
                warehouse = default_profile.warehouse_name
            else:
                frappe.throw("No warehouse specified and no default POS profile with warehouse found")

        conditions = ["item.disabled = 0", "item.is_sales_item = 1"]
        values = []
        
        if search_term:
            conditions.append("(item.item_code LIKE %s OR item.item_name LIKE %s)")
            search_pattern = f"%{search_term}%"
            values.extend([search_pattern, search_pattern])
        
        # Build the query using Stock Ledger Entry
        query = f"""
            SELECT 
                item.item_code,
                item.item_name,
                item.item_group,
                item.standard_rate,
                item.item_image,
                item.description,
                COALESCE(sle_summary.stock_qty, 0) as stock_qty,
                item.unit_of_measurement
            FROM `tabItem` item
            LEFT JOIN (
                SELECT 
                    item as item_code,
                    SUM(actual_qty) as stock_qty
                FROM `tabStock Ledger Entry`
                WHERE warehouse = %s
                GROUP BY item
            ) sle_summary ON item.item_code = sle_summary.item_code
            WHERE {' AND '.join(conditions)}
            ORDER BY item.item_name
            LIMIT 100
        """
        
        values.append(warehouse)
        items = frappe.db.sql(query, values, as_dict=True)
        
        return items
        
    except Exception as e:
        frappe.log_error(f"Error in get_pos_items: {str(e)}")
        return []


@frappe.whitelist()
def get_item_stock(item_code, warehouse):
    """Get current stock level for an item"""
    try:
        # Calculate stock from Stock Ledger Entry
        stock_qty = frappe.db.sql("""
            SELECT COALESCE(SUM(actual_qty), 0) as stock_qty
            FROM `tabStock Ledger Entry`
            WHERE item = %s AND warehouse = %s
        """, (item_code, warehouse), as_dict=True)[0].stock_qty or 0
        
        return {"item_code": item_code, "stock_qty": stock_qty}
        
    except Exception as e:
        frappe.log_error(f"Error in get_item_stock: {str(e)}")
        return {"item_code": item_code, "stock_qty": 0}


@frappe.whitelist()
def validate_stock_availability(items, warehouse):
    """Validate if sufficient stock is available for all items"""
    try:
        validation_results = []
        
        for item in items:
            item_code = item.get("item_code")
            required_qty = flt(item.get("qty"))
            
            # Calculate available quantity from Stock Ledger Entry
            available_qty = frappe.db.sql("""
                SELECT COALESCE(SUM(actual_qty), 0) as stock_qty
                FROM `tabStock Ledger Entry`
                WHERE item = %s AND warehouse = %s
            """, (item_code, warehouse), as_dict=True)[0].stock_qty or 0
            
            is_valid = available_qty >= required_qty
            
            validation_results.append({
                "item_code": item_code,
                "required_qty": required_qty,
                "available_qty": available_qty,
                "is_valid": is_valid,
                "message": f"Required: {required_qty}, Available: {available_qty}" if not is_valid else "OK"
            })
        
        return {
            "is_valid": all(result["is_valid"] for result in validation_results),
            "results": validation_results
        }
        
    except Exception as e:
        frappe.log_error(f"Error in validate_stock_availability: {str(e)}")
        return {"is_valid": False, "error": str(e)}


@frappe.whitelist()
def get_customer_details(customer_name):
    """Get customer details for POS"""
    try:
        if not customer_name or customer_name == "Walk-in Customer":
            return {
                "customer_name": "Walk-in Customer",
                "customer_type": "Individual",
                "territory": "Algeria"
            }
        
        customer = frappe.get_doc("Customer", customer_name)
        return {
            "customer_name": customer.customer_name,
            "customer_type": customer.customer_type,
            "territory": customer.territory,
            "customer_group": customer.customer_group
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_customer_details: {str(e)}")
        return None


@frappe.whitelist()
def search_customers(search_term):
    """Search customers for POS"""
    try:
        customers = frappe.get_all(
            "Customer",
            filters=[
                ["customer_name", "like", f"%{search_term}%"]
            ],
            fields=["name", "customer_name", "customer_type"],
            limit=10
        )
        
        # Always include Walk-in Customer
        walk_in = {
            "name": "Walk-in Customer",
            "customer_name": "Walk-in Customer",
            "customer_type": "Individual"
        }
        
        if walk_in not in customers:
            customers.insert(0, walk_in)
        
        return customers
        
    except Exception as e:
        frappe.log_error(f"Error in search_customers: {str(e)}")
        return [{"name": "Walk-in Customer", "customer_name": "Walk-in Customer", "customer_type": "Individual"}]


@frappe.whitelist()
def get_pos_reports_data(from_date=None, to_date=None, pos_profile=None):
    """Get POS reports data"""
    try:
        if not from_date:
            from_date = nowdate()
        if not to_date:
            to_date = nowdate()
        
        conditions = ["pi.docstatus = 1"]
        values = []
        
        conditions.append("pi.posting_date BETWEEN %s AND %s")
        values.extend([from_date, to_date])
        
        if pos_profile:
            conditions.append("pi.pos_profile = %s")
            values.append(pos_profile)
        
        # Sales summary
        sales_query = f"""
            SELECT 
                COUNT(*) as total_invoices,
                SUM(pi.grand_total) as total_sales,
                SUM(pi.total_qty) as total_qty,
                AVG(pi.grand_total) as avg_sale_value
            FROM `tabPOS Invoice` pi
            WHERE {' AND '.join(conditions)}
        """
        
        sales_data = frappe.db.sql(sales_query, values, as_dict=True)[0]
        
        # Top selling items
        items_query = f"""
            SELECT 
                pii.item_code,
                pii.item_name,
                SUM(pii.qty) as total_qty,
                SUM(pii.amount) as total_amount
            FROM `tabPOS Invoice Item` pii
            INNER JOIN `tabPOS Invoice` pi ON pi.name = pii.parent
            WHERE {' AND '.join(conditions)}
            GROUP BY pii.item_code, pii.item_name
            ORDER BY total_amount DESC
            LIMIT 10
        """
        
        top_items = frappe.db.sql(items_query, values, as_dict=True)
        
        # Payment method summary
        payment_query = f"""
            SELECT 
                pip.payment_method,
                SUM(pip.amount) as total_amount,
                COUNT(*) as transaction_count
            FROM `tabPOS Invoice Payment` pip
            INNER JOIN `tabPOS Invoice` pi ON pi.name = pip.parent
            WHERE {' AND '.join(conditions)}
            GROUP BY pip.payment_method
            ORDER BY total_amount DESC
        """
        
        payment_summary = frappe.db.sql(payment_query, values, as_dict=True)
        
        return {
            "sales_summary": sales_data,
            "top_items": top_items,
            "payment_summary": payment_summary,
            "date_range": {"from_date": from_date, "to_date": to_date}
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_pos_reports_data: {str(e)}")
        return {"error": str(e)}