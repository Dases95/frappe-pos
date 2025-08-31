frappe.ui.form.on('Delivery Note', {
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
                    // Check if inventory.pricing is available
                    if (typeof inventory !== 'undefined' && inventory.pricing) {
                        // Use pricing utility to get customer-specific prices
                        inventory.pricing.get_item_price(item.item, true, customer, null, function(rate, price_list) {
                            if(rate > 0) {
                                frappe.model.set_value("Delivery Note Item", item.name, "rate", rate);
                                updated_items++;
                                
                                if(idx === frm.doc.items.length - 1 && updated_items > 0) {
                                    frappe.msgprint(`Updated pricing for ${updated_items} items based on customer ${customer}`);
                                }
                            }
                        });
                    } else {
                        // Fallback to basic item price retrieval if utility is not available
                        get_basic_selling_price(item.item, customer, function(rate, price_source) {
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
                                    let summary = `Updated pricing for ${updated_items} items based on customer ${customer}:\n`;
                                    for (let source in price_sources) {
                                        let source_label = "";
                                        switch(source) {
                                            case "customer-specific":
                                                source_label = "customer-specific prices";
                                                break;
                                            case "default-selling":
                                                source_label = "default selling prices";
                                                break;
                                            case "default-both":
                                                source_label = "default prices (buy/sell)";
                                                break;
                                            case "general":
                                                source_label = "general selling prices";
                                                break;
                                            case "valuation":
                                                source_label = "valuation rates with markup";
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

// Basic function to get selling prices if the inventory.pricing utility is not available
function get_basic_selling_price(item_code, customer, callback) {
    // First try customer-specific price
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
            fields: ["price_list_rate"],
            order_by: "modified desc",
            limit: 1
        },
        callback: function(r) {
            if(r.message && r.message.length > 0) {
                callback(r.message[0].price_list_rate, "customer-specific");
            } else {
                // Try default selling price
                frappe.call({
                    method: "frappe.client.get_list",
                    args: {
                        doctype: "Item Price",
                        filters: {
                            "item_code": item_code,
                            "selling": 1,
                            "buying": 0,
                            "is_default_price": 1,
                            "enabled": 1
                        },
                        fields: ["price_list_rate"],
                        order_by: "modified desc",
                        limit: 1
                    },
                    callback: function(r) {
                        if(r.message && r.message.length > 0) {
                            callback(r.message[0].price_list_rate, "default-selling");
                        } else {
                            // Try default buying+selling price
                            frappe.call({
                                method: "frappe.client.get_list",
                                args: {
                                    doctype: "Item Price",
                                    filters: {
                                        "item_code": item_code,
                                        "selling": 1,
                                        "buying": 1,
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
                                        // Try general price (no customer and not default)
                                        frappe.call({
                                            method: "frappe.client.get_list",
                                            args: {
                                                doctype: "Item Price",
                                                filters: {
                                                    "item_code": item_code,
                                                    "selling": 1,
                                                    "customer": ["in", ["", null]],
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
                                                    // Try getting from the item's valuation rate with a markup
                                                    frappe.db.get_value('Item', item_code, ['valuation_rate'], function(item_values) {
                                                        if(item_values && item_values.valuation_rate) {
                                                            // Apply a 20% markup on valuation rate as fallback
                                                            let markup_rate = flt(item_values.valuation_rate) * 1.2;
                                                            callback(markup_rate, "valuation");
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