frappe.ui.form.on('Purchase Receipt', {
    refresh: function(frm) {
        // Set query filters for Item
        frm.set_query("item", "items", function() {
            return {
                filters: {
                    disabled: 0
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
        calculate_total_amount(frm);
    },
    
    // When supplier is changed, update prices for all items
    supplier: function(frm) {
        if(frm.doc.supplier && frm.doc.items && frm.doc.items.length) {
            let updated_items = 0;
            let supplier = frm.doc.supplier;
            let price_sources = {};
            
            frm.doc.items.forEach(function(item, idx) {
                if(item.item) {
                    // Check if inventory.pricing is available
                    if (typeof inventory !== 'undefined' && inventory.pricing) {
                        // Use pricing utility to get supplier-specific prices
                        inventory.pricing.get_item_price(item.item, false, null, supplier, function(rate, price_list) {
                            if(rate > 0) {
                                frappe.model.set_value("Purchase Receipt Item", item.name, "rate", rate);
                                updated_items++;
                                
                                if(idx === frm.doc.items.length - 1 && updated_items > 0) {
                                    frappe.msgprint(`Updated pricing for ${updated_items} items based on supplier ${supplier}`);
                                }
                            }
                        });
                    } else {
                        // Fallback to basic item price retrieval if utility is not available
                        get_basic_item_price(item.item, supplier, function(rate, price_source) {
                            if(rate > 0) {
                                frappe.model.set_value("Purchase Receipt Item", item.name, "rate", rate);
                                updated_items++;
                                
                                // Keep track of price sources
                                if (!price_sources[price_source]) {
                                    price_sources[price_source] = 0;
                                }
                                price_sources[price_source]++;
                                
                                // Show summary after all items are processed
                                if(idx === frm.doc.items.length - 1 && updated_items > 0) {
                                    let summary = `Updated pricing for ${updated_items} items based on supplier ${supplier}:\n`;
                                    for (let source in price_sources) {
                                        let source_label = "";
                                        switch(source) {
                                            case "supplier-specific":
                                                source_label = "supplier-specific prices";
                                                break;
                                            case "default-buying":
                                                source_label = "default buying prices";
                                                break;
                                            case "default-both":
                                                source_label = "default prices (buy/sell)";
                                                break;
                                            case "general":
                                                source_label = "general buying prices";
                                                break;
                                            case "historical":
                                                source_label = "historical purchase rates";
                                                break;
                                            default:
                                                source_label = source;
                                        }
                                        summary += `- ${price_sources[source]} items using ${source_label}\n`;
                                    }
                                    frappe.msgprint(summary);
                                }
                            }
                        });
                    }
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
        if(row.item && frm.doc.supplier) {
            // Check if inventory.pricing is available
            if (typeof inventory !== 'undefined' && inventory.pricing) {
                // When item is selected, get supplier-specific price
                inventory.pricing.get_item_price(row.item, false, null, frm.doc.supplier, function(rate, price_list) {
                    if(rate > 0) {
                        frappe.model.set_value(cdt, cdn, "rate", rate);
                        
                        let message = `Price applied: ${rate}`;
                        if(price_list) {
                            message = `Price applied from Price List: ${price_list}`;
                            if(frm.doc.supplier) {
                                message += ` for supplier ${frm.doc.supplier}`;
                            }
                        } else {
                            message = "Applied historical purchase price as no price list was found.";
                        }
                        frappe.msgprint(message);
                    } else {
                        // If no price found, allow manual entry
                        frappe.msgprint("No price found for this item. Please enter the rate manually.");
                    }
                });
            } else {
                // Fallback to basic item price retrieval if utility is not available
                get_basic_item_price(row.item, frm.doc.supplier, function(rate, price_source) {
                    if(rate > 0) {
                        frappe.model.set_value(cdt, cdn, "rate", rate);
                        
                        let message = "";
                        switch(price_source) {
                            case "supplier-specific":
                                message = `Applied supplier-specific price: ${rate} for ${frm.doc.supplier}`;
                                break;
                            case "default-buying":
                                message = `Applied default buying price: ${rate}`;
                                break;
                            case "default-both":
                                message = `Applied default price: ${rate}`;
                                break;
                            case "general":
                                message = `Applied general buying price: ${rate}`;
                                break;
                            case "historical":
                                message = `Applied historical purchase rate: ${rate}`;
                                break;
                            default:
                                message = `Applied price: ${rate}`;
                        }
                        frappe.msgprint(message);
                    } else {
                        frappe.msgprint("No price found for this item. Please enter the rate manually.");
                    }
                });
            }
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

// Basic function to get item prices if the inventory.pricing utility is not available
function get_basic_item_price(item_code, supplier, callback) {
    // First try supplier-specific price
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
            fields: ["price_list_rate"],
            order_by: "modified desc",
            limit: 1
        },
        callback: function(r) {
            if(r.message && r.message.length > 0) {
                callback(r.message[0].price_list_rate, "supplier-specific");
            } else {
                // Try default buying price
                frappe.call({
                    method: "frappe.client.get_list",
                    args: {
                        doctype: "Item Price",
                        filters: {
                            "item_code": item_code,
                            "buying": 1,
                            "selling": 0,
                            "is_default_price": 1,
                            "enabled": 1
                        },
                        fields: ["price_list_rate"],
                        order_by: "modified desc",
                        limit: 1
                    },
                    callback: function(r) {
                        if(r.message && r.message.length > 0) {
                            callback(r.message[0].price_list_rate, "default-buying");
                        } else {
                            // Try default buying+selling price
                            frappe.call({
                                method: "frappe.client.get_list",
                                args: {
                                    doctype: "Item Price",
                                    filters: {
                                        "item_code": item_code,
                                        "buying": 1,
                                        "selling": 1,
                                        "is_default_price": 1,
                                        "enabled": 1
                                    },
                                    fields: ["price_list_rate"],
                                    order_by: "modified desc",
                                    limit: 1
                                },
                                callback: function(r) {
                                    if(r.message && r.message.length > 0) {
                                        callback(r.message[0].price_list_rate, "default-both");
                                    } else {
                                        // Try general price (no supplier and not default)
                                        frappe.call({
                                            method: "frappe.client.get_list",
                                            args: {
                                                doctype: "Item Price",
                                                filters: {
                                                    "item_code": item_code,
                                                    "buying": 1,
                                                    "supplier": ["in", ["", null]],
                                                    "is_default_price": 0,
                                                    "enabled": 1
                                                },
                                                fields: ["price_list_rate"],
                                                order_by: "modified desc",
                                                limit: 1
                                            },
                                            callback: function(r) {
                                                if(r.message && r.message.length > 0) {
                                                    callback(r.message[0].price_list_rate, "general");
                                                } else {
                                                    // Try getting from the item's last purchase rate
                                                    frappe.db.get_value('Item', item_code, ['last_purchase_rate', 'valuation_rate'], function(item_values) {
                                                        if(item_values) {
                                                            let rate = item_values.last_purchase_rate || item_values.valuation_rate || 0;
                                                            callback(rate, "historical");
                                                        } else {
                                                            callback(0, "none");
                                                        }
                                                    });
                                                }
                                            }
                                        });
                                    }
                                }
                            });
                        }
                    }
                });
            }
        }
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