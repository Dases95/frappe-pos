frappe.ui.form.on('Sales Order', {
    refresh: function(frm) {
        // Add custom buttons
        if(frm.doc.docstatus === 1) {
            frm.add_custom_button(__('Create Delivery Note'), function() {
                frappe.model.open_mapped_doc({
                    method: "inventory.inventory.doctype.sales_order.sales_order.make_delivery_note",
                    frm: frm
                });
            }, __("Create"));
            
            if(frm.doc.status !== "Completed") {
                frm.add_custom_button(__('Update Status'), function() {
                    let d = new frappe.ui.Dialog({
                        title: 'Update Status',
                        fields: [
                            {
                                label: 'Status',
                                fieldname: 'status',
                                fieldtype: 'Select',
                                options: 'Ordered\nPartially Delivered\nCompleted',
                                default: frm.doc.status
                            }
                        ],
                        primary_action_label: 'Update',
                        primary_action: function(values) {
                            frappe.call({
                                method: "update_status",
                                doc: frm.doc,
                                args: {
                                    status: values.status
                                },
                                callback: function(r) {
                                    if (!r.exc) {
                                        frm.reload_doc();
                                        frappe.show_alert({
                                            message: __("Status updated successfully"),
                                            indicator: 'green'
                                        });
                                    }
                                }
                            });
                            d.hide();
                        }
                    });
                    d.show();
                });
            }
        }
    },
    
    customer: function(frm) {
        // When customer changes, update all item rates
        if (frm.doc.customer && frm.doc.items) {
            frm.doc.items.forEach(function(item) {
                if (item.item) {
                    get_item_rate(frm, item);
                }
            });
        }
    },
    
    order_date: function(frm) {
        // When order date changes, update all item rates
        if (frm.doc.customer && frm.doc.items) {
            frm.doc.items.forEach(function(item) {
                if (item.item) {
                    get_item_rate(frm, item);
                }
            });
        }
    },
    
    barcode_search: function(frm) {
        // Handle barcode search and add item to table
        if (frm.doc.barcode_search) {
            if (!frm.doc.customer) {
                frappe.msgprint({
                    title: __('Customer Required'),
                    message: __('Please select a customer first'),
                    indicator: 'orange'
                });
                frm.set_value('barcode_search', '');
                return;
            }
            
            let search_value = frm.doc.barcode_search;
            
            // Search for item by barcode, item code, or item name
            frappe.call({
                method: "inventory.inventory.doctype.sales_order.sales_order.search_item_by_barcode",
                args: {
                    search_value: search_value
                },
                callback: function(r) {
                    if (r.message && r.message.item_code) {
                        // Check if item already exists in the table
                        let existing_item = frm.doc.items.find(item => item.item === r.message.item_code);
                        
                        if (existing_item) {
                            // Item exists, increment quantity
                            frappe.model.set_value(existing_item.doctype, existing_item.name, 'quantity', (existing_item.quantity || 0) + 1);
                            
                            frappe.show_alert({
                                message: __('Quantity updated for {0}', [r.message.item_name]),
                                indicator: 'blue'
                            }, 2);
                        } else {
                            // Add new item row
                            let row = frm.add_child('items');
                            row.item = r.message.item_code;
                            row.quantity = 1;
                            
                            // Refresh the items table
                            frm.refresh_field('items');
                            
                            // Get the rate for the newly added item
                            get_item_rate(frm, row);
                            
                            frappe.show_alert({
                                message: __('Item {0} added', [r.message.item_name]),
                                indicator: 'green'
                            }, 2);
                        }
                        
                        // Clear the search field
                        frm.set_value('barcode_search', '');
                        
                        // Focus back on barcode search field for next scan
                        setTimeout(function() {
                            frm.fields_dict.barcode_search.$input.focus();
                        }, 100);
                        
                    } else if (r.message && r.message.error) {
                        frappe.msgprint({
                            title: __('Item Not Found'),
                            message: r.message.error,
                            indicator: 'red'
                        });
                        frm.set_value('barcode_search', '');
                    }
                },
                error: function(r) {
                    frappe.msgprint({
                        title: __('Error'),
                        message: __('Failed to search for item'),
                        indicator: 'red'
                    });
                    frm.set_value('barcode_search', '');
                }
            });
        }
    },
    
    // Calculate amount when quantity or rate changes
    items_on_form_rendered: function(frm) {
        // Calculate item amount and total
        frm.doc.items.forEach(function(item) {
            item.amount = item.quantity * item.rate;
        });
        
        let total_amount = 0;
        frm.doc.items.forEach(function(item) {
            total_amount += item.amount;
        });
        frm.set_value("total_amount", total_amount);
    },
    
    // Set rates from price list when item is selected
    setup: function(frm) {
        frm.add_fetch("customer", "customer_type", "customer_type");
        
        // Use custom query that supports barcode search
        frm.set_query("item", "items", function() {
            return {
                query: "inventory.inventory.doctype.sales_order.sales_order.item_query",
                filters: {
                    disabled: 0
                }
            };
        });
    }
});

// Child table events for Sales Order Item
frappe.ui.form.on('Sales Order Item', {
    item: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.item && frm.doc.customer) {
            get_item_rate(frm, row);
        }
    },
    
    quantity: function(frm, cdt, cdn) {
        calculate_item_amount(frm, cdt, cdn);
    },
    
    rate: function(frm, cdt, cdn) {
        calculate_item_amount(frm, cdt, cdn);
    }
});

// Helper function to get item rate from Item Price
function get_item_rate(frm, item) {
    if (!item.item || !frm.doc.customer) {
        return;
    }
    
    frappe.call({
        method: "inventory.inventory.doctype.sales_order.sales_order.get_item_price",
        args: {
            item_code: item.item,
            customer: frm.doc.customer,
            transaction_date: frm.doc.order_date || frappe.datetime.get_today()
        },
        callback: function(r) {
            if (r.message) {
                if (r.message.rate) {
                    frappe.model.set_value(item.doctype, item.name, 'rate', r.message.rate);
                    
                    // Show info message about which price was used
                    if (r.message.price_type === 'customer_specific') {
                        frappe.show_alert({
                            message: __('Customer-specific price applied for {0}', [item.item]),
                            indicator: 'blue'
                        }, 3);
                    } else if (r.message.price_type === 'default') {
                        frappe.show_alert({
                            message: __('Default price applied for {0}', [item.item]),
                            indicator: 'green'
                        }, 3);
                    }
                } else if (r.message.error) {
                    // Show error message
                    frappe.msgprint({
                        title: __('No Sales Price Found'),
                        message: r.message.error,
                        indicator: 'red'
                    });
                    
                    // Clear the rate
                    frappe.model.set_value(item.doctype, item.name, 'rate', 0);
                }
            }
        }
    });
}

// Helper function to calculate item amount
function calculate_item_amount(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    let amount = (row.quantity || 0) * (row.rate || 0);
    frappe.model.set_value(cdt, cdn, 'amount', amount);
    
    // Calculate total
    let total_amount = 0;
    frm.doc.items.forEach(function(item) {
        total_amount += (item.amount || 0);
    });
    frm.set_value("total_amount", total_amount);
} 