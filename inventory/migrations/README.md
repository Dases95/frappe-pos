# Price List to Item Price Migration

This directory contains scripts to migrate from the separate Price List and Item Price doctypes to a merged Item Price doctype that incorporates price list functionality.

## Migration Process

1. **Backup your database** before proceeding.

2. Apply the schema changes to the Item Price doctype JSON, Python, and JavaScript files.

3. Run the migration script:
   ```
   bench --site your-site-name execute inventory.inventory.migrations.price_list_to_item_price.execute
   ```

4. Verify the migration by checking Item Price records. Each record should now have a `price_list_name` field populated with the name from the original Price List doctype.

5. Update any custom code or reports that reference the Price List doctype.

6. After successful testing in a non-production environment, you can remove the Price List doctype and price_list_name field:
   ```
   bench --site your-site-name execute inventory.inventory.migrations.delete_price_list_doctype.execute
   bench --site your-site-name execute inventory.inventory.migrations.remove_price_list_name_field.execute
   ```

## Complete Removal Process

The complete process to remove the Price List doctype and its references involves:

1. Apply the schema changes to remove price_list_name from the Item Price doctype:
   - Update JSON file
   - Update JS file
   - Update Python file

2. Delete Price List doctype and remove fields from database:
   ```
   bench --site your-site-name execute inventory.inventory.migrations.delete_price_list_doctype.execute
   bench --site your-site-name execute inventory.inventory.migrations.remove_price_list_name_field.execute
   ```

3. Rebuild client files and clear cache:
   ```
   bench build
   bench clear-cache
   ```

## Post-Migration Tasks

1. Update any documents or doctypes that reference the Price List doctype:
   - Sales Order
   - Purchase Order
   - Quotation
   - etc.

2. Create list views/reports with the updated Item Price doctype to show:
   - All prices for a specific item
   - All buying/selling prices
   - Customer/supplier specific pricing

## Handling References in Code

After migration, any code that previously referenced the Price List doctype should be updated:

```python
# Old code
price_list = frappe.get_doc("Price List", "Standard Selling")
item_prices = frappe.get_all("Item Price", filters={"price_list": "Standard Selling"})

# New code - filter by buying/selling flags instead
item_prices = frappe.get_all("Item Price", 
                           filters={"selling": 1, "enabled": 1},
                           fields=["name", "item_code", "currency", "price_list_rate"])
```

## Troubleshooting

If you encounter issues during migration or deletion:

1. Check the migration log output for any errors
2. Verify that all Item Price records have been updated correctly
3. If deletion scripts fail, check for any remaining references to the Price List doctype
4. Always have a backup available to restore if needed 