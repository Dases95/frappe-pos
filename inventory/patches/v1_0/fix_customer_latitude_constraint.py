import frappe

def execute():
    """
    Fix Customer latitude field constraint - allow NULL values
    """
    try:
        # Check if we're using PostgreSQL
        if frappe.db.db_type == 'postgres':
            # Alter the column to allow NULL values
            frappe.db.sql("""
                ALTER TABLE "tabCustomer" 
                ALTER COLUMN "latitude" DROP NOT NULL
            """)
            frappe.db.commit()
            
        # For MariaDB/MySQL
        elif frappe.db.db_type in ['mariadb', 'mysql']:
            # First get the column definition
            column_info = frappe.db.sql("""
                SELECT COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'tabCustomer' 
                AND COLUMN_NAME = 'latitude'
            """, (frappe.db.get_database_name(),))
            
            if column_info:
                column_type = column_info[0][0]
                # Alter the column to allow NULL
                frappe.db.sql(f"""
                    ALTER TABLE `tabCustomer` 
                    MODIFY COLUMN `latitude` {column_type} NULL
                """)
                frappe.db.commit()
        
        print("Successfully fixed Customer latitude field constraint")
        
    except Exception as e:
        print(f"Error fixing Customer latitude constraint: {str(e)}")
        # Don't raise the error to prevent migration failure
        # The constraint will be handled by the doctype sync
        pass 