# Algeria Test Data Generator

This guide explains how to create comprehensive test data for the Algerian market using the inventory app's built-in commands.

## Overview

The Algeria test data generator creates realistic business data specifically tailored for the Algerian market, including:

- **Customers**: Individuals and companies with authentic Algerian names
- **Suppliers**: Local businesses from major Algerian cities
- **Products**: Items commonly found in the Algerian market (food, textiles, electronics, construction materials)
- **Warehouses**: Storage facilities in major Algerian cities
- **Transactions**: Sample sales and purchase orders with realistic data

## Prerequisites

1. **Install Geography Data First**:
   ```bash
   bench --site your-site-name inventory install-geography
   ```
   This installs all 48 Wilayas (provinces) and their communes (municipalities).

2. **Ensure Site is Active**:
   ```bash
   bench use your-site-name
   ```

## Creating Test Data

### Basic Command

```bash
bench --site your-site-name inventory create-algeria-test-data
```

This creates:
- 50 customers
- 20 suppliers
- All predefined Algerian products (~20 items)
- 8 warehouses in major cities
- 100 transactions (50 sales orders + 50 purchase orders)

### Custom Parameters

```bash
bench --site your-site-name inventory create-algeria-test-data \
  --customers 100 \
  --suppliers 30 \
  --items 15 \
  --transactions 200
```

**Parameters:**
- `--customers`: Number of customers to create (default: 50)
- `--suppliers`: Number of suppliers to create (default: 20)
- `--items`: Number of items to create (default: all predefined items)
- `--transactions`: Number of transactions to create (default: 100)

## Generated Data Details

### Customers
- **Names**: Authentic Algerian first and last names
- **Types**: 70% individuals, 30% companies
- **Addresses**: Distributed across all 48 Wilayas
- **Contact**: Mobile numbers and email addresses
- **Territories**: Mapped to Algerian provinces

### Suppliers
- **Names**: Realistic Algerian company names
- **Locations**: Major Algerian cities
- **Contact**: Business phone numbers and email addresses
- **Type**: Local suppliers

### Products
- **Food Items**: كسكس, زيت الزيتون, تمر دقلة نور, قمح صلب, etc.
- **Textiles**: قماش قطني, صوف طبيعي, حرير
- **Electronics**: هاتف ذكي, حاسوب محمول, تلفزيون
- **Construction**: إسمنت, حديد التسليح, رمل, حصى
- **Pricing**: Realistic price ranges in Algerian Dinars
- **Stock**: Random opening stock quantities

### Warehouses
Created in major Algerian cities:
- الجزائر العاصمة (Algiers)
- وهران (Oran)
- قسنطينة (Constantine)
- عنابة (Annaba)
- باتنة (Batna)
- سطيف (Setif)
- سيدي بلعباس (Sidi Bel Abbès)
- بسكرة (Biskra)

### Transactions
- **Sales Orders**: Random customers, 1-5 items per order
- **Purchase Orders**: Random suppliers, 1-5 items per order
- **Dates**: Distributed over the last 90 days
- **Pricing**: Realistic variations (sales +10%, purchases -20%)

## Data Management

### View Statistics

```bash
bench --site your-site-name inventory show-geography-stats
```

Shows:
- Total Wilayas and Communes
- Top 5 Wilayas by commune count

### Clear Test Data

⚠️ **Warning**: This deletes ALL data, use with extreme caution!

```bash
bench --site your-site-name inventory clear-test-data --confirm
```

Without `--confirm` flag, you'll be prompted for confirmation.

## Usage Examples

### 1. Small Dataset for Development
```bash
bench --site dev-site inventory create-algeria-test-data \
  --customers 20 \
  --suppliers 5 \
  --items 10 \
  --transactions 30
```

### 2. Large Dataset for Testing
```bash
bench --site test-site inventory create-algeria-test-data \
  --customers 200 \
  --suppliers 50 \
  --transactions 500
```

### 3. Product-Focused Dataset
```bash
bench --site product-site inventory create-algeria-test-data \
  --customers 30 \
  --suppliers 10 \
  --items 25 \
  --transactions 100
```

## Integration with POS

The generated data works seamlessly with the Point of Sale system:

1. **Customers**: Available for selection in POS transactions
2. **Products**: Appear in the product grid with stock quantities
3. **Warehouses**: Can be selected as POS warehouse
4. **Pricing**: Items have realistic standard rates

## Customization

To customize the data generation:

1. **Edit Product List**: Modify `ALGERIAN_PRODUCTS` in `/inventory/commands/test_data.py`
2. **Add Names**: Extend `ALGERIAN_FIRST_NAMES`, `ALGERIAN_LAST_NAMES`, or `ALGERIAN_COMPANIES`
3. **Modify Pricing**: Adjust price ranges in the product definitions
4. **Add Cities**: Include more cities in the warehouse creation function

## Troubleshooting

### Common Issues

1. **"No Wilayas found" Warning**:
   ```bash
   bench --site your-site-name inventory install-geography
   ```

2. **Permission Errors**:
   Ensure you're running as the frappe user and the site exists.

3. **Duplicate Data**:
   The script checks for existing records and skips duplicates.

4. **Memory Issues with Large Datasets**:
   Create data in smaller batches:
   ```bash
   # Create in multiple runs
   bench --site your-site inventory create-algeria-test-data --customers 50 --transactions 0
   bench --site your-site inventory create-algeria-test-data --customers 0 --transactions 100
   ```

### Verification

After creating test data, verify in the system:

1. **Check Customer List**: Go to Selling > Customer
2. **Check Item List**: Go to Stock > Item
3. **Check Transactions**: Go to Selling > Sales Order
4. **Test POS**: Go to Point of Sale and verify products load

## Data Cleanup

For development/testing cycles:

```bash
# Clear all test data
bench --site your-site inventory clear-test-data --confirm

# Recreate fresh data
bench --site your-site inventory create-algeria-test-data
```

## Support

For issues or customization requests:
1. Check the command output for specific error messages
2. Verify prerequisites are met
3. Review the generated data in the Frappe interface
4. Check system logs for detailed error information

---

**Note**: All generated data is for testing purposes only and should not be used in production environments without proper review and modification.