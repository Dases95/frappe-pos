frappe.ui.form.on('Item Group', {
    refresh: function(frm) {
        // Setup filters for item selection in the child table
        frm.set_query("item", "items", function() {
            return {
                filters: {
                    disabled: 0
                }
            };
        });
    }
}); 