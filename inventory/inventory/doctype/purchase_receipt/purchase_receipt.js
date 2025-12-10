frappe.ui.form.on('Purchase Receipt', {
    refresh: function(frm) {
        // Set query filters for Item - exclude already selected items
        frm.set_query("item", "items", function(doc, cdt, cdn) {
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
                    "item": d.item
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
            
            if(frm.doc.purchase_order) {
                frm.add_custom_button(__('Purchase Order'), function() {
                    frappe.set_route("Form", "Purchase Order", frm.doc.purchase_order);
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
    
    // When supplier is changed, update prices for all items
    supplier: function(frm) {
        if(frm.doc.supplier && frm.doc.items && frm.doc.items.length) {
            let supplier = frm.doc.supplier;
            
            frm.doc.items.forEach(function(item) {
                if(item.item) {
                    get_item_buying_price(item.item, supplier, function(rate, price_source) {
                        if(rate > 0) {
                            frappe.model.set_value("Purchase Receipt Item", item.name, "rate", rate);
                        }
                    });
                }
            });
        }
    },
    
    // When Purchase Order is selected, fetch items
    purchase_order: function(frm) {
        if(frm.doc.purchase_order) {
            frappe.call({
                method: "frappe.client.get",
                args: {
                    doctype: "Purchase Order",
                    name: frm.doc.purchase_order
                },
                callback: function(r) {
                    if(r.message) {
                        let po = r.message;
                        frm.set_value("supplier", po.supplier);
                        
                        // Clear existing items
                        frm.clear_table("items");
                        
                        // Add items from Purchase Order
                        po.items.forEach(function(item) {
                            let pr_item = frm.add_child("items");
                            pr_item.item = item.item;
                            pr_item.quantity = item.quantity;
                            pr_item.rate = item.rate;
                            pr_item.amount = item.amount;
                            pr_item.purchase_order = frm.doc.purchase_order;
                        });
                        
                        frm.refresh_field("items");
                        calculate_total_amount(frm);
                    }
                }
            });
        }
    }
});

// Purchase Receipt Item child table events
frappe.ui.form.on('Purchase Receipt Item', {
    items_add: function(frm, cdt, cdn) {
        calculate_total_amount(frm);
    },
    
    items_remove: function(frm, cdt, cdn) {
        calculate_total_amount(frm);
    },
    
    item: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if(row.item) {
            let supplier = frm.doc.supplier || null;
            // Fetch price for the item
            get_item_buying_price(row.item, supplier, function(rate, price_source) {
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
    
    quantity: function(frm, cdt, cdn) {
        calculate_item_amount(frm, cdt, cdn);
        calculate_total_amount(frm);
    },
    
    rate: function(frm, cdt, cdn) {
        calculate_item_amount(frm, cdt, cdn);
        calculate_total_amount(frm);
    },
    
    amount: function(frm, cdt, cdn) {
        calculate_total_amount(frm);
    }
});

/**
 * Get item buying price with priority:
 * 1. Supplier-specific buying price (if supplier is provided)
 * 2. Default buying price (is_default_price=1, buying=1)
 * 3. General buying price (no supplier, not default)
 * 4. Last purchase rate or valuation rate as last resort
 */
function get_item_buying_price(item_code, supplier, callback) {
    let today = frappe.datetime.get_today();
    
    // Step 1: Try supplier-specific price first (if supplier is provided)
    if(supplier) {
        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Item Price",
                filters: {
                    "item_code": item_code,
                    "buying": 1,
                    "supplier": supplier,
                    "enabled": 1
                },
                fields: ["price_list_rate", "valid_from", "valid_upto"],
                order_by: "is_default_price desc, modified desc",
                limit: 1
            },
            callback: function(r) {
                if(r.message && r.message.length > 0) {
                    let price = r.message[0];
                    if(is_price_valid(price, today)) {
                        callback(price.price_list_rate, "supplier-specific");
                        return;
                    }
                }
                // No valid supplier-specific price, try default
                get_default_buying_price(item_code, today, callback);
            }
        });
    } else {
        // No supplier, go directly to default price
        get_default_buying_price(item_code, today, callback);
    }
}

/**
 * Check if price is valid for given date
 */
function is_price_valid(price, today) {
    let valid_from = price.valid_from;
    let valid_upto = price.valid_upto;
    
    if(valid_from && valid_from > today) {
        return false;
    }
    
    if(valid_upto && valid_upto < today) {
        return false;
    }
    
    return true;
}

/**
 * Get default buying price
 */
function get_default_buying_price(item_code, today, callback) {
    frappe.call({
        method: "frappe.client.get_list",
        args: {
            doctype: "Item Price",
            filters: {
                "item_code": item_code,
                "buying": 1,
                "is_default_price": 1,
                "enabled": 1
            },
            fields: ["price_list_rate", "selling", "valid_from", "valid_upto"],
            order_by: "selling asc, modified desc",
            limit: 5
        },
        callback: function(r) {
            if(r.message && r.message.length > 0) {
                for(let price of r.message) {
                    if(is_price_valid(price, today)) {
                        let price_source = price.selling ? "default-both" : "default-buying";
                        callback(price.price_list_rate, price_source);
                        return;
                    }
                }
            }
            // No valid default price, try general buying price
            get_general_buying_price(item_code, today, callback);
        }
    });
}

/**
 * Get general buying price (no supplier, not default)
 */
function get_general_buying_price(item_code, today, callback) {
    frappe.call({
        method: "frappe.client.get_list",
        args: {
            doctype: "Item Price",
            filters: {
                "item_code": item_code,
                "buying": 1,
                "enabled": 1
            },
            fields: ["price_list_rate", "valid_from", "valid_upto", "supplier"],
            order_by: "modified desc",
            limit: 10
        },
        callback: function(r) {
            if(r.message && r.message.length > 0) {
                for(let price of r.message) {
                    if(!price.supplier && is_price_valid(price, today)) {
                        callback(price.price_list_rate, "general");
                        return;
                    }
                }
            }
            // No valid general price, try last purchase rate
            get_historical_rate(item_code, callback);
        }
    });
}

/**
 * Get last purchase rate or valuation rate as last resort
 */
function get_historical_rate(item_code, callback) {
    frappe.db.get_value('Item', item_code, ['last_purchase_rate', 'valuation_rate'], function(item_values) {
        if(item_values) {
            let rate = item_values.last_purchase_rate || item_values.valuation_rate || 0;
            if(rate > 0) {
                callback(rate, "historical");
                return;
            }
        }
        callback(0, "none");
    });
}

// Calculate amount for a single item
function calculate_item_amount(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    if (row.quantity && row.rate) {
        frappe.model.set_value(cdt, cdn, 'amount', flt(row.quantity) * flt(row.rate));
    } else {
        frappe.model.set_value(cdt, cdn, 'amount', 0);
    }
}

// Calculate total amount for all items
function calculate_total_amount(frm) {
    let total_amount = 0;
    if(frm.doc.items && frm.doc.items.length) {
        frm.doc.items.forEach(function(item) {
            if(item.amount) {
                total_amount += flt(item.amount);
            }
        });
    }
    frm.set_value("total_amount", total_amount);
} 