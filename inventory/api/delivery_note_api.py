import frappe
from frappe import _
from frappe.utils import cint, flt, getdate, now_datetime
from frappe.utils.response import build_response

@frappe.whitelist()
def list_delivery_notes():
    """
    Get a list of all delivery notes
    
    Returns:
        dict: List of delivery notes with basic info
    """
    try:
        delivery_notes = frappe.get_all(
            "Delivery Note",
            fields=["name", "customer", "customer_name", "delivery_date", "total_amount", "docstatus"],
            order_by="modified desc"
        )
        
        return {
            "success": True,
            "data": delivery_notes
        }
    except Exception as e:
        frappe.log_error(f"Error in list_delivery_notes: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to retrieve delivery notes: {str(e)}"
        }

@frappe.whitelist()
def get_delivery_note(delivery_note_id):
    """
    Get delivery note details by ID
    
    Args:
        delivery_note_id (str): The delivery note ID
        
    Returns:
        dict: Delivery note details with items
    """
    try:
        if not delivery_note_id:
            return {
                "success": False,
                "message": "Delivery note ID is required"
            }
        
        # Get delivery note document
        delivery_note = frappe.get_doc("Delivery Note", delivery_note_id)
        
        # Convert to dict for API response
        delivery_note_dict = delivery_note.as_dict()
        
        return {
            "success": True,
            "data": delivery_note_dict
        }
    except frappe.DoesNotExistError:
        return {
            "success": False,
            "message": f"Delivery note {delivery_note_id} not found"
        }
    except Exception as e:
        frappe.log_error(f"Error in get_delivery_note: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to retrieve delivery note: {str(e)}"
        }

@frappe.whitelist()
def create_delivery_note():
    """
    Create a new delivery note
    
    Request Body:
        customer (str): Customer ID
        delivery_date (str): Delivery date in YYYY-MM-DD format
        sales_order (str, optional): Sales Order ID
        items (list): List of items with item_code, quantity, rate
        remarks (str, optional): Remarks
        
    Returns:
        dict: Created delivery note details
    """
    try:
        data = frappe.local.form_dict
        
        # Debug: Log received data
        frappe.logger().info(f"Received delivery note data: {data}")
        
        # Validate required fields
        if not data.get("customer"):
            return {
                "success": False,
                "message": "Customer is required"
            }
        
        # Handle items - if it's a string (from FormData), parse it as JSON
        items = data.get("items")
        frappe.logger().info(f"Raw items data: {items}, type: {type(items)}")
        
        if isinstance(items, str):
            try:
                import json
                items = json.loads(items)
                frappe.logger().info(f"Parsed items: {items}")
            except (json.JSONDecodeError, ValueError) as e:
                frappe.logger().error(f"Failed to parse items JSON: {str(e)}")
                return {
                    "success": False,
                    "message": f"Invalid items format: {str(e)}"
                }
        
        if not items or not isinstance(items, list):
            frappe.logger().error(f"Items validation failed: items={items}, type={type(items)}")
            return {
                "success": False,
                "message": "Items are required and must be a list"
            }
        
        # Create delivery note
        dn = frappe.new_doc("Delivery Note")
        dn.customer = data.get("customer")
        dn.delivery_date = data.get("delivery_date") or getdate()
        dn.posting_time = data.get("posting_time") or now_datetime().strftime("%H:%M:%S")
        
        if data.get("sales_order"):
            dn.sales_order = data.get("sales_order")
        
        if data.get("remarks"):
            dn.remarks = data.get("remarks")
        
        # Add items
        for item_data in items:
            if not item_data.get("item"):
                continue
                
            item = dn.append("items", {})
            item.item = item_data.get("item")
            item.quantity = flt(item_data.get("quantity") or 1)
            item.rate = flt(item_data.get("rate") or 0)
            
            # If batch is provided and item has batch tracking
            if item_data.get("batch"):
                item.batch = item_data.get("batch")
                
            # If coming from sales order, link it
            if data.get("sales_order") and item_data.get("sales_order_item"):
                item.sales_order = data.get("sales_order")
                item.sales_order_item = item_data.get("sales_order_item")
        
        # Save and submit if auto_submit is True
        dn.insert()
        
        if cint(data.get("auto_submit")):
            dn.submit()
        
        return {
            "success": True,
            "message": "Delivery Note created successfully",
            "data": {
                "name": dn.name,
                "customer": dn.customer,
                "delivery_date": dn.delivery_date,
                "total_amount": dn.total_amount,
                "docstatus": dn.docstatus
            }
        }
    except Exception as e:
        frappe.log_error(f"Error in create_delivery_note: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to create delivery note: {str(e)}"
        }

@frappe.whitelist()
def update_delivery_note(delivery_note_id):
    """
    Update an existing delivery note
    
    Args:
        delivery_note_id (str): The delivery note ID
        
    Request Body:
        delivery_date (str, optional): Delivery date in YYYY-MM-DD format
        remarks (str, optional): Remarks
        items (list, optional): List of items to update
        
    Returns:
        dict: Updated delivery note details
    """
    try:
        data = frappe.local.form_dict
        
        if not delivery_note_id:
            return {
                "success": False,
                "message": "Delivery note ID is required"
            }
        
        # Get delivery note
        dn = frappe.get_doc("Delivery Note", delivery_note_id)
        
        # Check if document is already submitted
        if dn.docstatus == 1:
            return {
                "success": False,
                "message": "Cannot update a submitted delivery note"
            }
        
        # Update fields
        if data.get("delivery_date"):
            dn.delivery_date = data.get("delivery_date")
        
        if data.get("remarks"):
            dn.remarks = data.get("remarks")
        
        # Update or add items
        if data.get("items") and isinstance(data.get("items"), list):
            # First, keep track of existing items
            existing_items = {item.name: item for item in dn.items}
            updated_items = set()
            
            for item_data in data.get("items"):
                if item_data.get("name") and item_data.get("name") in existing_items:
                    # Update existing item
                    item = existing_items[item_data.get("name")]
                    
                    if item_data.get("quantity"):
                        item.quantity = flt(item_data.get("quantity"))
                    
                    if item_data.get("rate"):
                        item.rate = flt(item_data.get("rate"))
                    
                    if item_data.get("batch"):
                        item.batch = item_data.get("batch")
                    
                    updated_items.add(item_data.get("name"))
                else:
                    # Add new item
                    if not item_data.get("item"):
                        continue
                        
                    item = dn.append("items", {})
                    item.item = item_data.get("item")
                    item.quantity = flt(item_data.get("quantity") or 1)
                    item.rate = flt(item_data.get("rate") or 0)
                    
                    if item_data.get("batch"):
                        item.batch = item_data.get("batch")
            
            # Remove items that were not updated or added
            for idx, item in enumerate(list(dn.items)):
                if hasattr(item, 'name') and item.name and item.name not in updated_items:
                    if item_data.get("remove_items", []) and item.name in item_data.get("remove_items"):
                        dn.items.remove(item)
        
        # Save
        dn.save()
        
        return {
            "success": True,
            "message": "Delivery Note updated successfully",
            "data": {
                "name": dn.name,
                "customer": dn.customer,
                "delivery_date": dn.delivery_date,
                "total_amount": dn.total_amount,
                "docstatus": dn.docstatus
            }
        }
    except frappe.DoesNotExistError:
        return {
            "success": False,
            "message": f"Delivery note {delivery_note_id} not found"
        }
    except Exception as e:
        frappe.log_error(f"Error in update_delivery_note: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to update delivery note: {str(e)}"
        }

@frappe.whitelist()
def delete_delivery_note(delivery_note_id):
    """
    Delete a delivery note
    
    Args:
        delivery_note_id (str): The delivery note ID
        
    Returns:
        dict: Status of the deletion operation
    """
    try:
        if not delivery_note_id:
            return {
                "success": False,
                "message": "Delivery note ID is required"
            }
        
        # Get delivery note
        dn = frappe.get_doc("Delivery Note", delivery_note_id)
        
        # Check if document is already submitted
        if dn.docstatus == 1:
            return {
                "success": False,
                "message": "Cannot delete a submitted delivery note. Cancel it first."
            }
        
        # Delete the document
        frappe.delete_doc("Delivery Note", delivery_note_id)
        
        return {
            "success": True,
            "message": f"Delivery note {delivery_note_id} deleted successfully"
        }
    except frappe.DoesNotExistError:
        return {
            "success": False,
            "message": f"Delivery note {delivery_note_id} not found"
        }
    except Exception as e:
        frappe.log_error(f"Error in delete_delivery_note: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to delete delivery note: {str(e)}"
        }

@frappe.whitelist()
def submit_delivery_note(delivery_note_id):
    """
    Submit a delivery note
    
    Args:
        delivery_note_id (str): The delivery note ID
        
    Returns:
        dict: Status of the submission operation
    """
    try:
        if not delivery_note_id:
            return {
                "success": False,
                "message": "Delivery note ID is required"
            }
        
        # Get delivery note
        dn = frappe.get_doc("Delivery Note", delivery_note_id)
        
        # Check if document is already submitted
        if dn.docstatus == 1:
            return {
                "success": False,
                "message": "Delivery note is already submitted"
            }
        
        # Submit the document
        dn.submit()
        
        return {
            "success": True,
            "message": f"Delivery note {delivery_note_id} submitted successfully",
            "data": {
                "name": dn.name,
                "docstatus": dn.docstatus
            }
        }
    except frappe.DoesNotExistError:
        return {
            "success": False,
            "message": f"Delivery note {delivery_note_id} not found"
        }
    except Exception as e:
        frappe.log_error(f"Error in submit_delivery_note: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to submit delivery note: {str(e)}"
        }

@frappe.whitelist()
def cancel_delivery_note(delivery_note_id):
    """
    Cancel a delivery note
    
    Args:
        delivery_note_id (str): The delivery note ID
        
    Returns:
        dict: Status of the cancellation operation
    """
    try:
        if not delivery_note_id:
            return {
                "success": False,
                "message": "Delivery note ID is required"
            }
        
        # Get delivery note
        dn = frappe.get_doc("Delivery Note", delivery_note_id)
        
        # Check if document is already cancelled
        if dn.docstatus == 2:
            return {
                "success": False,
                "message": "Delivery note is already cancelled"
            }
        
        # Check if document is submitted
        if dn.docstatus != 1:
            return {
                "success": False,
                "message": "Only submitted delivery notes can be cancelled"
            }
        
        # Cancel the document
        dn.cancel()
        
        return {
            "success": True,
            "message": f"Delivery note {delivery_note_id} cancelled successfully",
            "data": {
                "name": dn.name,
                "docstatus": dn.docstatus
            }
        }
    except frappe.DoesNotExistError:
        return {
            "success": False,
            "message": f"Delivery note {delivery_note_id} not found"
        }
    except Exception as e:
        frappe.log_error(f"Error in cancel_delivery_note: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to cancel delivery note: {str(e)}"
        }

@frappe.whitelist()
def get_delivery_notes_for_customer(customer_id):
    """
    Get all delivery notes for a specific customer
    
    Args:
        customer_id (str): The customer ID
        
    Returns:
        dict: List of delivery notes for the customer
    """
    try:
        if not customer_id:
            return {
                "success": False,
                "message": "Customer ID is required"
            }
        
        delivery_notes = frappe.get_all(
            "Delivery Note",
            filters={"customer": customer_id},
            fields=["name", "delivery_date", "total_amount", "docstatus"],
            order_by="delivery_date desc"
        )
        
        return {
            "success": True,
            "data": delivery_notes
        }
    except Exception as e:
        frappe.log_error(f"Error in get_delivery_notes_for_customer: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to retrieve delivery notes: {str(e)}"
        }

@frappe.whitelist()
def get_delivery_note_items_from_sales_order(sales_order_id):
    """
    Get items from a sales order to create a delivery note
    
    Args:
        sales_order_id (str): The sales order ID
        
    Returns:
        dict: Sales order items with details for delivery note creation
    """
    try:
        if not sales_order_id:
            return {
                "success": False,
                "message": "Sales Order ID is required"
            }
        
        # Check if sales order exists
        if not frappe.db.exists("Sales Order", sales_order_id):
            return {
                "success": False,
                "message": f"Sales Order {sales_order_id} not found"
            }
        
        # Get sales order
        so = frappe.get_doc("Sales Order", sales_order_id)
        
        # Get customer details
        customer_info = {
            "customer": so.customer,
            "customer_name": so.customer_name
        }
        
        # Get items
        items = []
        for item in so.items:
            # Get delivered quantity
            delivered_qty = frappe.db.sql("""
                SELECT SUM(dni.quantity)
                FROM `tabDelivery Note Item` dni
                JOIN `tabDelivery Note` dn ON dni.parent = dn.name
                WHERE dni.sales_order = %s
                AND dni.item = %s
                AND dn.docstatus = 1
            """, (sales_order_id, item.item), as_dict=0)
            
            delivered_qty = flt(delivered_qty[0][0]) if delivered_qty and delivered_qty[0][0] else 0
            pending_qty = flt(item.quantity) - delivered_qty
            
            if pending_qty > 0:
                items.append({
                    "item": item.item,
                    "item_name": item.item_name,
                    "quantity": pending_qty,
                    "rate": item.rate,
                    "uom": item.uom,
                    "sales_order": sales_order_id,
                    "sales_order_item": item.name
                })
        
        return {
            "success": True,
            "data": {
                "customer_info": customer_info,
                "items": items
            }
        }
    except Exception as e:
        frappe.log_error(f"Error in get_delivery_note_items_from_sales_order: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to retrieve sales order items: {str(e)}"
        } 