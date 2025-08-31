frappe.ui.form.on('Item Price', {
    refresh: function(frm) {
        // Set filters for item field
        frm.set_query("item_code", function() {
            return {
                filters: {
                    "disabled": 0
                }
            };
        });
        
        // Set filters for customer field - use status field instead of disabled
        frm.set_query("customer", function() {
            return {
                filters: {
                    "status": "Active"
                }
            };
        });
        
        // Set filters for supplier field - use status field instead of disabled
        frm.set_query("supplier", function() {
            return {
                filters: {
                    "status": "Active"
                }
            };
        });
        
        // Update field visibility based on buying/selling and is_default_price
        update_field_visibility(frm);
        
        // Add a button to view similar prices
        frm.add_custom_button(__('Similar Item Prices'), function() {
            frappe.route_options = {'item_code': frm.doc.item_code};
            frappe.set_route('List', 'Item Price');
        }, __("View"));
    },
    
    buying: function(frm) {
        // If buying is unchecked and selling is also unchecked, set selling to true
        if (!frm.doc.buying && !frm.doc.selling) {
            frm.set_value("selling", 1);
        }
        
        update_field_visibility(frm);
    },
    
    selling: function(frm) {
        // If selling is unchecked and buying is also unchecked, set buying to true
        if (!frm.doc.selling && !frm.doc.buying) {
            frm.set_value("buying", 1);
        }
        
        update_field_visibility(frm);
    },

    is_default_price: function(frm) {
        // If is_default_price is checked, clear the supplier field
        if (frm.doc.is_default_price) {
            frm.set_value("supplier", "");
            
            // Get price type description for messages
            let price_type = frm.doc.buying && frm.doc.selling ? "buying and selling" : 
                             frm.doc.buying ? "buying" : "selling";
            
            // Show information message
            frappe.msgprint(__(`This will be set as the default ${price_type} price for this item.`));
        }
        
        update_field_visibility(frm);
    }
});

// Helper function to control field visibility based on buying/selling flags and is_default_price
function update_field_visibility(frm) {
    // Show/hide customer field based on selling flag
    if (frm.doc.selling) {
        frm.set_df_property("customer", "hidden", 0);
    } else {
        frm.set_df_property("customer", "hidden", 1);
        frm.set_value("customer", "");
    }
    
    // Show/hide supplier field based on buying flag AND is_default_price
    if (frm.doc.buying && !frm.doc.is_default_price) {
        frm.set_df_property("supplier", "hidden", 0);
    } else {
        frm.set_df_property("supplier", "hidden", 1);
        frm.set_value("supplier", "");
    }
    
    // Always show is_default_price (for both buying and selling)
    frm.set_df_property("is_default_price", "hidden", 0);
} 