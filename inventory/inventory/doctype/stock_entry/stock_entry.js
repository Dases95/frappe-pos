frappe.ui.form.on('Stock Entry', {
    refresh: function(frm) {
        frm.set_query("item", "items", function() {
            return {
                filters: {
                    disabled: 0
                }
            };
        });
        
        frm.set_query("batch", "items", function(doc, cdt, cdn) {
            let d = locals[cdt][cdn];
            if(!d.item) {
                frappe.throw(__("Please select Item first"));
            }
            return {
                filters: {
                    "item": d.item
                }
            };
        });
    },
    
    entry_type: function(frm) {
        // Hide/show fields based on entry type
        // Issue and Sale require source warehouse (stock going out)
        // Receipt, Purchase, Transfer, Manufacture require target warehouse (stock coming in)
        frm.toggle_reqd("source_warehouse", ["Issue", "Sale", "Transfer"].includes(frm.doc.entry_type));
        frm.toggle_reqd("target_warehouse", ["Receipt", "Purchase", "Transfer", "Manufacture"].includes(frm.doc.entry_type));
        
        if (frm.doc.entry_type === "Receipt" || frm.doc.entry_type === "Purchase") {
            frm.set_value("source_warehouse", "");
        } else if (frm.doc.entry_type === "Issue" || frm.doc.entry_type === "Sale") {
            frm.set_value("target_warehouse", "");
        }
    },
    
    validate: function(frm) {
        calculate_total_amount(frm);
    },

    item_group: function(frm) {
        if(frm.doc.item_group) {
            // Clear existing items before adding new ones
            frappe.confirm(
                __('Do you want to load items from the selected item group? This will replace any existing items.'),
                function() {
                    // If user confirms, fetch and add items
                    frm.clear_table('items');
                    frappe.call({
                        method: 'frappe.client.get',
                        args: {
                            doctype: 'Item Group',
                            name: frm.doc.item_group
                        },
                        callback: function(r) {
                            if(r.message && r.message.items) {
                                $.each(r.message.items, function(i, d) {
                                    var child = frm.add_child('items');
                                    child.item = d.item;
                                    child.item_name = d.item_name;
                                    child.quantity = d.default_quantity || 1;
                                    child.rate = d.default_rate || 0;
                                    child.amount = child.quantity * child.rate;
                                });
                                frm.refresh_field('items');
                                calculate_total_amount(frm);
                            }
                        }
                    });
                }
            );
        }
    }
});

frappe.ui.form.on('Stock Entry Item', {
    items_add: function(frm, cdt, cdn) {
        calculate_total_amount(frm);
    },
    
    items_remove: function(frm, cdt, cdn) {
        calculate_total_amount(frm);
    },
    
    amount: function(frm, cdt, cdn) {
        calculate_total_amount(frm);
    },
    
    quantity: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        row.amount = flt(row.quantity) * flt(row.rate);
        frm.refresh_field('items');
        calculate_total_amount(frm);
    },
    
    rate: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        row.amount = flt(row.quantity) * flt(row.rate);
        frm.refresh_field('items');
        calculate_total_amount(frm);
    }
});

function calculate_total_amount(frm) {
    let total = 0;
    if(frm.doc.items && frm.doc.items.length) {
        frm.doc.items.forEach(function(item) {
            if(item.amount) {
                total += flt(item.amount);
            }
        });
    }
    frm.set_value("total_amount", total);
} 