import frappe

def execute():
    """
    Delete the Price List doctype now that its functionality 
    has been merged into the Item Price doctype
    """
    frappe.flags.in_migrate = True
    
    # Step 1: Check if there are any remaining Item Price records with price_list or price_list_name
    # This is a safety check to ensure migration has completed
    has_old_references = False
    
    # Check if price_list field exists
    if "price_list" in frappe.db.get_table_columns("Item Price"):
        price_list_references = frappe.db.sql("""
            SELECT name FROM `tabItem Price` 
            WHERE price_list IS NOT NULL AND price_list != ''
        """)
        
        if price_list_references and len(price_list_references) > 0:
            has_old_references = True
            print(f"WARNING: {len(price_list_references)} Item Price records still have price_list references")
    
    # Check if price_list_name field exists
    if "price_list_name" in frappe.db.get_table_columns("Item Price"):
        price_list_name_references = frappe.db.sql("""
            SELECT name FROM `tabItem Price` 
            WHERE price_list_name IS NOT NULL AND price_list_name != ''
        """)
        
        if price_list_name_references and len(price_list_name_references) > 0:
            has_old_references = True
            print(f"WARNING: {len(price_list_name_references)} Item Price records still have price_list_name references")
    
    if has_old_references:
        print("Not proceeding with deletion due to existing references. Please run the migration script first.")
        return
    
    # Step 2: Delete the Price List doctype if it exists
    if frappe.db.exists("DocType", "Price List"):
        # Delete all Price List records first
        frappe.db.sql("DELETE FROM `tabPrice List`")
        print("Deleted all Price List records")
        
        # Delete the DocType
        frappe.delete_doc("DocType", "Price List", force=1)
        print("Deleted Price List DocType")
    else:
        print("Price List DocType does not exist or has already been deleted")
    
    print("Price List deletion completed successfully")
    
    frappe.flags.in_migrate = False

if __name__ == "__main__":
    execute() 