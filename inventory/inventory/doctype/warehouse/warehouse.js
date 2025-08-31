frappe.ui.form.on('Warehouse', {
    refresh: function(frm) {
        // Add custom buttons
        frm.add_custom_button(__('Stock Balance'), function() {
            frappe.route_options = {
                "warehouse": frm.doc.name
            };
            frappe.set_route("query-report", "Stock Balance");
        }, __("View"));
    }
}); 