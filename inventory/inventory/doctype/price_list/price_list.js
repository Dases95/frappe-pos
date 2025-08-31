frappe.ui.form.on('Price List', {
    refresh: function(frm) {
        frm.set_query("item", "items", function() {
            return {
                filters: {
                    disabled: 0
                }
            };
        });

        // Add a button to view all Item Prices for this price list
        frm.add_custom_button(__('Item Prices'), function() {
            frappe.route_options = {'price_list': frm.doc.name};
            frappe.set_route('List', 'Item Price');
        }, __("View"));
    },
    
    buying: function(frm) {
        // If buying is unchecked and selling is also unchecked, set selling to true
        if (!frm.doc.buying && !frm.doc.selling) {
            frm.set_value("selling", 1);
        }
    },
    
    selling: function(frm) {
        // If selling is unchecked and buying is also unchecked, set buying to true
        if (!frm.doc.selling && !frm.doc.buying) {
            frm.set_value("buying", 1);
        }
    }
}); 