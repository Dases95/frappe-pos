frappe.ui.form.on('Sales Order', {
    refresh: function(frm) {
        // Add custom buttons
        if(frm.doc.docstatus === 1) {
            frm.add_custom_button(__('Create Delivery Note'), function() {
                frappe.model.open_mapped_doc({
                    method: "inventory.inventory.doctype.sales_order.sales_order.make_delivery_note",
                    frm: frm
                });
            }, __("Create"));
            
            if(frm.doc.status !== "Completed") {
                frm.add_custom_button(__('Update Status'), function() {
                    let d = new frappe.ui.Dialog({
                        title: 'Update Status',
                        fields: [
                            {
                                label: 'Status',
                                fieldname: 'status',
                                fieldtype: 'Select',
                                options: 'Ordered\nPartially Delivered\nCompleted',
                                default: frm.doc.status
                            }
                        ],
                        primary_action_label: 'Update',
                        primary_action: function(values) {
                            frappe.call({
                                method: "update_status",
                                doc: frm.doc,
                                args: {
                                    status: values.status
                                },
                                callback: function(r) {
                                    if (!r.exc) {
                                        frm.reload_doc();
                                        frappe.show_alert({
                                            message: __("Status updated successfully"),
                                            indicator: 'green'
                                        });
                                    }
                                }
                            });
                            d.hide();
                        }
                    });
                    d.show();
                });
            }
        }
    },
    
    // Calculate amount when quantity or rate changes
    items_on_form_rendered: function(frm) {
        // Calculate item amount and total
        frm.doc.items.forEach(function(item) {
            item.amount = item.quantity * item.rate;
        });
        
        let total_amount = 0;
        frm.doc.items.forEach(function(item) {
            total_amount += item.amount;
        });
        frm.set_value("total_amount", total_amount);
    },
    
    // Set rates from price list when item is selected
    setup: function(frm) {
        frm.add_fetch("customer", "customer_type", "customer_type");
        
        frm.set_query("item", "items", function() {
            return {
                filters: {
                    disabled: 0
                }
            };
        });
    }
}); 