frappe.ui.form.on('Item', {
    refresh: function(frm) {
        // Add custom buttons
        frm.add_custom_button(__('Stock Balance'), function() {
            frappe.route_options = {
                "item_code": frm.doc.item_code
            };
            frappe.set_route("query-report", "Stock Balance");
        }, __("View"));

        frm.add_custom_button(__('Stock Ledger'), function() {
            frappe.route_options = {
                "item_code": frm.doc.item_code
            };
            frappe.set_route("query-report", "Stock Ledger");
        }, __("View"));
    },

    item_group: function(frm) {
        // Add logic when Item Group changes
        if (frm.doc.item_group === "Spice") {
            frm.set_value("requires_batch", 1);
            frm.set_value("has_expiry_date", 1);
        }
    }
}); 