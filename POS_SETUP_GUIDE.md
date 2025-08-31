# POS Module Setup Guide for Algerian Market

## Overview
This POS (Point of Sale) module is specifically designed for small and medium businesses in Algeria. It features:

- **Arabic/French Language Support**: Bilingual interface with Arabic RTL support
- **Algerian Dinar (DZD) Currency**: Pre-configured for local market
- **Simple Interface**: Clean, intuitive design for easy operation
- **No Tax Complications**: Simplified for businesses without complex tax requirements
- **Vue.js Frontend**: Modern, responsive interface
- **Session Management**: Daily session tracking and reconciliation
- **Receipt Printing**: Bilingual receipts in Arabic and French

## Installation Steps

### 1. Database Migration
Run the following commands to create the POS doctypes in your database:

```bash
cd /path/to/frappe-bench
bench --site your-site migrate
```

### 2. Initial Setup
Run the Algerian market configuration:

```bash
bench --site your-site execute inventory.pos.setup_data.create_default_pos_data
```

This will create:
- DZD currency
- Default payment methods (Cash, Card, Bank Transfer)
- Walk-in Customer
- POS roles (POS Manager, POS User)
- Sample POS profile

### 3. User Permissions
Assign appropriate roles to users:

- **POS Manager**: Full access to all POS operations and settings
- **POS User**: Access to POS interface for sales only
- **System Manager**: Complete administrative access

### 4. Configure POS Profile
1. Go to **POS > Setup > POS Profile**
2. Create or modify the "Main Store" profile:
   - Set your company
   - Select your warehouse
   - Configure payment methods
   - Set default currency to DZD

### 5. Create Items
Ensure your inventory items are configured with:
- Standard selling rates
- Stock tracking enabled
- Sales item flag checked

## Usage Guide

### Starting a POS Session

1. Navigate to `/app/point-of-sale`
2. Select your POS Profile
3. Enter opening cash amount
4. Click "Start Session"

### Making Sales

1. **Search Products**: Use the search bar to find items
2. **Add to Cart**: Click on products to add them to cart
3. **Adjust Quantities**: Use +/- buttons to modify quantities
4. **Select Payment Method**: Choose Cash, Card, or other methods
5. **Enter Payment Amount**: System calculates change automatically
6. **Complete Sale**: Click "Complete Sale" to finalize

### Closing Session

1. Click "Close Session" at the end of the day
2. The system will:
   - Calculate total sales
   - Show payment reconciliation
   - Generate closing report

### Receipt Printing

- Receipts are automatically generated after each sale
- Click "Print" to print receipt
- Receipts include bilingual thank you message

## Features

### Bilingual Support
- Toggle between English and Arabic using the language button
- RTL (Right-to-Left) support for Arabic text
- Algerian Dinar formatting with Arabic numerals

### Stock Management
- Real-time stock level display
- Automatic stock deduction on sales
- Stock validation before sale completion
- Configurable negative stock allowance

### Payment Processing
- Multiple payment methods support
- Cash change calculation
- Payment reconciliation at session close

### Reporting
- Daily sales summary
- POS session reports
- Payment method analysis
- Top-selling items tracking

## Algerian Market Configurations

### Currency Settings
- **Currency**: Algerian Dinar (DZD)
- **Symbol**: د.ج
- **Format**: #,###.## DZD

### Default Payment Methods
- **Cash** (النقد / Espèces) - Primary method
- **Card** (البطاقة / Carte) - Electronic payments
- **Bank Transfer** (تحويل بنكي / Virement) - Bank transfers

### Language Support
- **Arabic**: Right-to-left interface, Arabic number formatting
- **French**: Standard formatting for French users
- **English**: Default fallback language

## Troubleshooting

### Common Issues

**Issue**: No POS Profile found
**Solution**: Create a POS Profile and assign it to users

**Issue**: Items not showing in POS
**Solution**: Ensure items have:
- Standard selling rate set
- Disabled = 0
- Is Sales Item = 1

**Issue**: Stock errors
**Solution**: Check warehouse configuration and bin creation

**Issue**: Session won't start
**Solution**: Verify user has POS User role and POS Profile access

### API Endpoints
For custom integrations, the following API endpoints are available:

- `GET /api/method/inventory.pos.api.get_pos_data` - Get POS initialization data
- `POST /api/method/inventory.pos.doctype.pos_session.pos_session.create_opening_entry` - Start session
- `POST /api/method/inventory.pos.doctype.pos_invoice.pos_invoice.create_pos_invoice` - Create sale

## Customization

### Adding New Payment Methods
1. Go to **Accounts > Mode of Payment**
2. Create new payment method
3. Add to POS Profile payment methods table

### Customizing Receipt Format
Modify the `generateReceiptHTML()` function in `pos.js` to change receipt layout

### Adding New Languages
1. Update translations in `pos/setup_data.py`
2. Add language toggle in Vue.js interface
3. Update CSS for additional RTL languages

## Support

For technical support or customization requests:
- Check the error logs in **Settings > Error Log**
- Use Frappe's built-in help system
- Refer to Frappe documentation for advanced customizations

## Security Notes

- Ensure proper user role assignments
- Regularly backup POS transaction data
- Monitor session closing procedures
- Implement proper cash handling procedures

---

**Version**: 1.0
**Last Updated**: January 2024
**Compatibility**: Frappe v14+, ERPNext compatible 