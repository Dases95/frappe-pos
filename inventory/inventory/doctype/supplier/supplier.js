frappe.ui.form.on('Supplier', {
    refresh: function(frm) {
        // Add custom buttons
        frm.add_custom_button(__('Purchase Orders'), function() {
            frappe.route_options = {
                "supplier": frm.doc.name
            };
            frappe.set_route("List", "Purchase Order", "List");
        }, __("View"));
        
        frm.add_custom_button(__('Purchase Receipts'), function() {
            frappe.route_options = {
                "supplier": frm.doc.name
            };
            frappe.set_route("List", "Purchase Receipt", "List");
        }, __("View"));
    }
}); 