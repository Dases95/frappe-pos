frappe.ui.form.on('Delivery Note', {
    refresh: function(frm) {
        // Set query filters for Item - exclude already selected items
        frm.set_query("item", "items", function(doc, cdt, cdn) {
            // Get list of already selected items (excluding current row)
            let selected_items = [];
            let current_row = locals[cdt][cdn];
            
            if(doc.items && doc.items.length) {
                doc.items.forEach(function(item) {
                    if(item.item && item.name !== current_row.name) {
                        selected_items.push(item.item);
                    }
                });
            }
            
            return {
                filters: {
                    disabled: 0,
                    name: ["not in", selected_items]
                }
            };
        });
        
        // Set query filters for Batch based on Item
        frm.set_query("batch", "items", function(doc, cdt, cdn) {
            let d = locals[cdt][cdn];
            if(!d.item) {
                frappe.throw(__("Please select Item first"));
            }
            return {
                filters: {
                    "item": d.item,
                    "has_expired": 0
                }
            };
        });
        
        // Add custom buttons
        if(frm.doc.docstatus === 1) {
            frm.add_custom_button(__('Stock Entry'), function() {
                frappe.route_options = {
                    "reference_document": frm.doc.name
                };
                frappe.set_route("List", "Stock Entry", "List");
            }, __("View"));
            
            if(frm.doc.sales_order) {
                frm.add_custom_button(__('Sales Order'), function() {
                    frappe.set_route("Form", "Sales Order", frm.doc.sales_order);
                }, __("View"));
            }
        }
    },
    
    // Calculate total amount when form is loaded
    onload: function(frm) {
        calculate_total_amount(frm);
    },
    
    validate: function(frm) {
        // Check for duplicate items before saving
        if(frm.doc.items && frm.doc.items.length > 1) {
            let items_list = [];
            let duplicates = [];
            
            frm.doc.items.forEach(function(item) {
                if(item.item) {
                    if(items_list.includes(item.item)) {
                        if(!duplicates.includes(item.item)) {
                            duplicates.push(item.item);
                        }
                    } else {
                        items_list.push(item.item);
                    }
                }
            });
            
            if(duplicates.length > 0) {
                frappe.throw(__('Duplicate items found: {0}. Each item can only be added once.', [duplicates.join(', ')]));
            }
        }
        
        calculate_total_amount(frm);
    },
    
    // When customer is changed, update prices for all items
    customer: function(frm) {
        if(frm.doc.customer && frm.doc.items && frm.doc.items.length) {
            let updated_items = 0;
            let customer = frm.doc.customer;
            let price_sources = {};
            
            frm.doc.items.forEach(function(item, idx) {
                if(item.item) {
                    // Fallback to basic item price retrieval
                    get_item_selling_price(item.item, customer, function(rate, price_source) {
                        if(rate > 0) {
                            frappe.model.set_value("Delivery Note Item", item.name, "rate", rate);
                            updated_items++;
                            
                            // Keep track of price sources
                            if (!price_sources[price_source]) {
                                price_sources[price_source] = 0;
                            }
                            price_sources[price_source]++;
                            
                            // Show summary after all items are processed
                            if(idx === frm.doc.items.length - 1 && updated_items > 0) {
                                show_price_update_summary(updated_items, customer, price_sources);
                            }
                        }
                    });
                }
            });
        }
    },
    
    // When Sales Order is selected, fetch items
    sales_order: function(frm) {
        if(frm.doc.sales_order) {
            frappe.call({
                method: "frappe.client.get",
                args: {
                    doctype: "Sales Order",
                    name: frm.doc.sales_order
                },
                callback: function(r) {
                    if(r.message) {
                        let so = r.message;
                        frm.set_value("customer", so.customer);
                        
                        // Clear existing items
                        frm.clear_table("items");
                        
                        // Add items from Sales Order
                        so.items.forEach(function(item) {
                            let dn_item = frm.add_child("items");
                            dn_item.item = item.item;
                            dn_item.quantity = item.quantity;
                            dn_item.rate = item.rate;
                            dn_item.amount = item.amount;
                            dn_item.sales_order = frm.doc.sales_order;
                        });
                        
                        frm.refresh_field("items");
                        calculate_total_amount(frm);
                    }
                }
            });
        }
    }
});

// Child table events for Delivery Note Item
frappe.ui.form.on('Delivery Note Item', {
    // When item is selected, automatically fetch the price
    item: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if(row.item) {
            // Fetch price for the item
            let customer = frm.doc.customer || null;
            get_item_selling_price(row.item, customer, function(rate, price_source) {
                if(rate > 0) {
                    frappe.model.set_value(cdt, cdn, "rate", rate);
                    // Calculate amount if quantity exists
                    if(row.quantity) {
                        frappe.model.set_value(cdt, cdn, "amount", flt(row.quantity) * flt(rate));
                    }
                }
            });
        }
    },
    
    // Recalculate amount when quantity changes
    quantity: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if(row.quantity && row.rate) {
            frappe.model.set_value(cdt, cdn, "amount", flt(row.quantity) * flt(row.rate));
        }
        calculate_total_amount(frm);
    },
    
    // Recalculate amount when rate changes
    rate: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if(row.quantity && row.rate) {
            frappe.model.set_value(cdt, cdn, "amount", flt(row.quantity) * flt(row.rate));
        }
        calculate_total_amount(frm);
    },
    
    // Recalculate total when amount changes
    amount: function(frm, cdt, cdn) {
        calculate_total_amount(frm);
    },
    
    // Recalculate total when row is removed
    items_remove: function(frm) {
        calculate_total_amount(frm);
    }
});

/**
 * Get item selling price with priority:
 * 1. Customer-specific selling price (if customer is provided)
 * 2. Default selling price (is_default_price=1, selling=1)
 * 3. General selling price (no customer, not default)
 * 4. Valuation rate with markup as last resort
 */
function get_item_selling_price(item_code, customer, callback) {
    let today = frappe.datetime.get_today();
    
    // Step 1: Try customer-specific price first (if customer is provided)
    if(customer) {
        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Item Price",
                filters: {
                    "item_code": item_code,
                    "selling": 1,
                    "customer": customer,
                    "enabled": 1
                },
                fields: ["price_list_rate", "valid_from", "valid_upto"],
                order_by: "is_default_price desc, modified desc",
                limit: 1
            },
            callback: function(r) {
                if(r.message && r.message.length > 0) {
                    let price = r.message[0];
                    // Check validity dates
                    if(is_price_valid(price, today)) {
                        callback(price.price_list_rate, "customer-specific");
                        return;
                    }
                }
                // No valid customer-specific price, try default
                get_default_selling_price(item_code, today, callback);
            }
        });
    } else {
        // No customer, go directly to default price
        get_default_selling_price(item_code, today, callback);
    }
}

/**
 * Check if price is valid for given date
 */
function is_price_valid(price, today) {
    let valid_from = price.valid_from;
    let valid_upto = price.valid_upto;
    
    // Check valid_from
    if(valid_from && valid_from > today) {
        return false;
    }
    
    // Check valid_upto
    if(valid_upto && valid_upto < today) {
        return false;
    }
    
    return true;
}

/**
 * Step 2: Get default selling price
 */
function get_default_selling_price(item_code, today, callback) {
    frappe.call({
        method: "frappe.client.get_list",
        args: {
            doctype: "Item Price",
            filters: {
                "item_code": item_code,
                "selling": 1,
                "is_default_price": 1,
                "enabled": 1
            },
            fields: ["price_list_rate", "buying", "valid_from", "valid_upto"],
            order_by: "buying asc, modified desc",
            limit: 5
        },
        callback: function(r) {
            if(r.message && r.message.length > 0) {
                // Find first valid price
                for(let price of r.message) {
                    if(is_price_valid(price, today)) {
                        let price_source = price.buying ? "default-both" : "default-selling";
                        callback(price.price_list_rate, price_source);
                        return;
                    }
                }
            }
            // No valid default price, try general selling price
            get_general_selling_price(item_code, today, callback);
        }
    });
}

/**
 * Step 3: Get general selling price (no customer, not default)
 */
function get_general_selling_price(item_code, today, callback) {
    frappe.call({
        method: "frappe.client.get_list",
        args: {
            doctype: "Item Price",
            filters: {
                "item_code": item_code,
                "selling": 1,
                "enabled": 1
            },
            fields: ["price_list_rate", "valid_from", "valid_upto", "customer"],
            order_by: "modified desc",
            limit: 10
        },
        callback: function(r) {
            if(r.message && r.message.length > 0) {
                // Find first valid price without customer
                for(let price of r.message) {
                    if(!price.customer && is_price_valid(price, today)) {
                        callback(price.price_list_rate, "general");
                        return;
                    }
                }
            }
            // No valid general price, try valuation rate
            get_valuation_rate_price(item_code, callback);
        }
    });
}

/**
 * Step 4: Get valuation rate with markup as last resort
 */
function get_valuation_rate_price(item_code, callback) {
    frappe.db.get_value('Item', item_code, ['valuation_rate'], function(item_values) {
        if(item_values && item_values.valuation_rate) {
            // Apply 20% markup on valuation rate as fallback
            let markup_rate = flt(item_values.valuation_rate) * 1.2;
            callback(markup_rate, "valuation");
        } else {
            callback(0, "none");
        }
    });
}

/**
 * Show summary message for price updates
 */
function show_price_update_summary(updated_items, customer, price_sources) {
    let summary = __("Updated pricing for {0} items based on customer {1}:", [updated_items, customer]) + "\n";
    
    const source_labels = {
        "customer-specific": __("customer-specific prices"),
        "default-selling": __("default selling prices"),
        "default-both": __("default prices (buy/sell)"),
        "general": __("general selling prices"),
        "valuation": __("valuation rates with markup")
    };
    
    for (let source in price_sources) {
        let label = source_labels[source] || source;
        summary += __("- {0} items using {1}", [price_sources[source], label]) + "\n";
    }
    
    frappe.msgprint(summary);
}

// Calculate total amount for all items
function calculate_total_amount(frm) {
    let total_amount = 0;
    if(frm.doc.items && frm.doc.items.length) {
        frm.doc.items.forEach(function(item) {
            if(item.amount) {
                total_amount += flt(item.amount);
            } else if (item.quantity && item.rate) {
                item.amount = flt(item.quantity) * flt(item.rate);
                total_amount += item.amount;
            }
        });
    }
    frm.set_value("total_amount", total_amount);
} 