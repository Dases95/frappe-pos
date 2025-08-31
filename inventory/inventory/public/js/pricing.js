// Utility functions for handling pricing in the Inventory app

frappe.provide("inventory.pricing");

/**
 * Get the price for an item
 * @param {string} item - Item code
 * @param {boolean} is_selling - Whether this is for selling (true) or buying (false)
 * @param {string} customer - Customer code (optional, for selling prices)
 * @param {string} supplier - Supplier code (optional, for buying prices)
 * @param {function} callback - Callback function that receives (rate, price_list_name)
 */
inventory.pricing.get_item_price = function(item, is_selling, customer, supplier, callback) {
    if (!item) {
        if (callback) callback(0, null);
        return;
    }
    
    // Build filters for finding price
    let filters = {
        "item_code": item,
        [is_selling ? "selling" : "buying"]: 1,
        "valid_from": ["<=", frappe.datetime.get_today()],
        "valid_upto": [">=", frappe.datetime.get_today()]
    };
    
    // Add party-specific filters
    if (is_selling && customer) {
        filters.customer = customer;
    } else if (!is_selling && supplier) {
        filters.supplier = supplier;
    }
    
    // First try to get price from Item Price with valid dates and party-specific
    frappe.call({
        method: "frappe.client.get_list",
        args: {
            doctype: "Item Price",
            filters: filters,
            fields: ["price_list_rate", "price_list"],
            order_by: "modified desc"
        },
        callback: function(r) {
            // If we have valid party-specific price list items, use the first one
            if (r.message && r.message.length > 0) {
                if (callback) callback(r.message[0].price_list_rate, r.message[0].price_list);
            } else {
                // If no party-specific price found, try without party filter
                let general_filters = {
                    "item_code": item,
                    [is_selling ? "selling" : "buying"]: 1,
                    "valid_from": ["<=", frappe.datetime.get_today()],
                    "valid_upto": [">=", frappe.datetime.get_today()]
                };
                
                // Add condition to exclude party-specific prices
                if (is_selling) {
                    general_filters.customer = ["in", ["", null]];
                } else {
                    general_filters.supplier = ["in", ["", null]];
                }
                
                frappe.call({
                    method: "frappe.client.get_list",
                    args: {
                        doctype: "Item Price",
                        filters: general_filters,
                        fields: ["price_list_rate", "price_list"],
                        order_by: "modified desc"
                    },
                    callback: function(r) {
                        if (r.message && r.message.length > 0) {
                            if (callback) callback(r.message[0].price_list_rate, r.message[0].price_list);
                        } else {
                            // Try to find any price ignoring dates
                            try_find_any_price(item, is_selling, customer, supplier, callback);
                        }
                    }
                });
            }
        }
    });
};

/**
 * Helper function to try finding any price, ignoring date validity
 */
function try_find_any_price(item, is_selling, customer, supplier, callback) {
    // Try party-specific price first
    let filters = {
        "item_code": item,
        [is_selling ? "selling" : "buying"]: 1
    };
    
    // Add party-specific filters
    if (is_selling && customer) {
        filters.customer = customer;
    } else if (!is_selling && supplier) {
        filters.supplier = supplier;
    }
    
    frappe.call({
        method: "frappe.client.get_list",
        args: {
            doctype: "Item Price",
            filters: filters,
            fields: ["price_list_rate", "price_list"],
            order_by: "modified desc"
        },
        callback: function(r) {
            if (r.message && r.message.length > 0) {
                if (callback) callback(r.message[0].price_list_rate, r.message[0].price_list);
            } else {
                // Try general price (non-party specific)
                let general_filters = {
                    "item_code": item,
                    [is_selling ? "selling" : "buying"]: 1
                };
                
                // Add condition to exclude party-specific prices
                if (is_selling) {
                    general_filters.customer = ["in", ["", null]];
                } else {
                    general_filters.supplier = ["in", ["", null]];
                }
                
                frappe.call({
                    method: "frappe.client.get_list",
                    args: {
                        doctype: "Item Price",
                        filters: general_filters,
                        fields: ["price_list_rate", "price_list"],
                        order_by: "modified desc"
                    },
                    callback: function(r) {
                        if (r.message && r.message.length > 0) {
                            if (callback) callback(r.message[0].price_list_rate, r.message[0].price_list);
                        } else {
                            // Otherwise try to get from Item's last purchase/selling price or valuation
                            use_default_pricing(item, is_selling, callback);
                        }
                    }
                });
            }
        }
    });
}

/**
 * Helper function to use default pricing when no price list item is found
 */
function use_default_pricing(item, is_selling, callback) {
    frappe.db.get_value('Item', item, ['valuation_rate', 'last_purchase_rate'], (r) => {
        if (r) {
            let base_rate = r.last_purchase_rate || r.valuation_rate || 0;
            let final_rate = is_selling ? (base_rate * 1.2) : base_rate; // 20% markup for selling
            
            if (final_rate > 0) {
                if (callback) callback(final_rate, null);
            } else {
                if (callback) callback(0, null);
            }
        } else {
            if (callback) callback(0, null);
        }
    });
} 