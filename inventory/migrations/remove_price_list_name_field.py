import frappe

def execute():
    """
    Remove the price_list_name field from Item Price doctype
    after completing the merge of Price List into Item Price
    """
    frappe.flags.in_migrate = True
    
    # Check if the field exists in the table
    if "price_list_name" in frappe.db.get_table_columns("Item Price"):
        # First, check if any records still use this field meaningfully
        price_list_name_references = frappe.db.sql("""
            SELECT name FROM `tabItem Price` 
            WHERE price_list_name IS NOT NULL AND price_list_name != ''
        """)
        
        if price_list_name_references and len(price_list_name_references) > 0:
            print(f"WARNING: {len(price_list_name_references)} Item Price records still have price_list_name values.")
            print("Consider running a migration script first, or proceeding if these values are no longer needed.")
            
            # Uncomment the line below to clear the values instead of just warning
            # frappe.db.sql("UPDATE `tabItem Price` SET price_list_name = NULL")
            # print("Cleared price_list_name values from all Item Price records")
        
        # Drop the column
        frappe.db.sql("ALTER TABLE `tabItem Price` DROP COLUMN price_list_name")
        print("Removed price_list_name field from Item Price database table")
        
        # Also remove from DocField
        if frappe.db.exists("DocField", {"parent": "Item Price", "fieldname": "price_list_name"}):
            frappe.db.sql("""
                DELETE FROM `tabDocField` 
                WHERE parent = 'Item Price' AND fieldname = 'price_list_name'
            """)
            print("Removed price_list_name field from DocField")
        
        # Update the module def to refresh the schema
        frappe.clear_cache(doctype="Item Price")
        print("Cleared cache for Item Price doctype")
    else:
        print("price_list_name field does not exist in Item Price table or has already been removed")
    
    # Also check for any remaining price_list field
    if "price_list" in frappe.db.get_table_columns("Item Price"):
        frappe.db.sql("ALTER TABLE `tabItem Price` DROP COLUMN price_list")
        print("Removed price_list field from Item Price database table")
        
        # Also remove from DocField
        if frappe.db.exists("DocField", {"parent": "Item Price", "fieldname": "price_list"}):
            frappe.db.sql("""
                DELETE FROM `tabDocField` 
                WHERE parent = 'Item Price' AND fieldname = 'price_list'
            """)
            print("Removed price_list field from DocField")
    
    print("Field removal completed successfully")
    
    frappe.flags.in_migrate = False

if __name__ == "__main__":
    execute() 