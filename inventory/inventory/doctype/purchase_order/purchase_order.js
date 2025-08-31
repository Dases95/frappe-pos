frappe.ui.form.on('Purchase Order', {
    refresh: function(frm) {
        // Add custom buttons
        if(frm.doc.docstatus === 1) {
            frm.add_custom_button(__('Create Purchase Receipt'), function() {
                frappe.model.open_mapped_doc({
                    method: "inventory.inventory.doctype.purchase_order.purchase_order.make_purchase_receipt",
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
                                options: 'Ordered\nPartially Received\nCompleted',
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
    
    // Calculate total amount when form is loaded
    onload: function(frm) {
        calculate_total_amount(frm);
    },
    
    validate: function(frm) {
        calculate_total_amount(frm);
    }
});

// Purchase Order Item child table events
frappe.ui.form.on('Purchase Order Item', {
    items_add: function(frm, cdt, cdn) {
        calculate_total_amount(frm);
    },
    
    items_remove: function(frm, cdt, cdn) {
        calculate_total_amount(frm);
    },
    
    quantity: function(frm, cdt, cdn) {
        calculate_item_amount(frm, cdt, cdn);
        calculate_total_amount(frm);
    },
    
    rate: function(frm, cdt, cdn) {
        calculate_item_amount(frm, cdt, cdn);
        calculate_total_amount(frm);
    },
    
    amount: function(frm, cdt, cdn) {
        calculate_total_amount(frm);
    }
});

// Calculate amount for a single item
function calculate_item_amount(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    if (row.quantity && row.rate) {
        frappe.model.set_value(cdt, cdn, 'amount', flt(row.quantity) * flt(row.rate));
    } else {
        frappe.model.set_value(cdt, cdn, 'amount', 0);
    }
}

// Calculate total amount for all items
function calculate_total_amount(frm) {
    let total_amount = 0;
    if(frm.doc.items && frm.doc.items.length) {
        frm.doc.items.forEach(function(item) {
            if(item.amount) {
                total_amount += flt(item.amount);
            }
        });
    }
    frm.set_value("total_amount", total_amount);
} 