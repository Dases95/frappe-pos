frappe.ui.form.on('Batch', {
    refresh: function(frm) {
        // Add custom buttons
        frm.add_custom_button(__('Stock Balance'), function() {
            frappe.route_options = {
                "batch_id": frm.doc.name
            };
            frappe.set_route("query-report", "Stock Balance");
        }, __("View"));
        
        // Show expired indicator
        if (frm.doc.has_expired) {
            frm.page.set_indicator(__("Expired"), "red");
        } else if (frm.doc.expiry_date) {
            let days_to_expiry = frappe.datetime.get_diff(frm.doc.expiry_date, frappe.datetime.nowdate());
            if (days_to_expiry <= 30) {
                frm.page.set_indicator(__("Expires Soon"), "orange");
            } else {
                frm.page.set_indicator(__("Active"), "green");
            }
        } else {
            frm.page.set_indicator(__("Active"), "green");
        }
    }
}); 