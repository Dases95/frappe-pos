frappe.ui.form.on('Purchase Order Item', {
    item: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.item) {
            // Get the supplier from the parent Purchase Order
            let supplier = null;
            if (frm.doc.parent) {
                let purchase_order = frappe.get_doc(frm.doc.parenttype, frm.doc.parent);
                if (purchase_order && purchase_order.supplier) {
                    supplier = purchase_order.supplier;
                }
            }
            
            // Use the pricing utility to get the price
            inventory.pricing.get_item_price(row.item, false, null, supplier, function(rate, price_list) {
                frappe.model.set_value(cdt, cdn, 'rate', rate);
                if (price_list) {
                    let message = `Price applied from Price List: ${price_list}`;
                    if (supplier) {
                        message += ` for supplier ${supplier}`;
                    }
                    frappe.msgprint(message);
                } else if (rate > 0) {
                    frappe.msgprint("No price list rate found. Applied historical purchase price.");
                }
            });
        }
    },
    
    quantity: function(frm, cdt, cdn) {
        calculate_amount(frm, cdt, cdn);
    },
    
    rate: function(frm, cdt, cdn) {
        calculate_amount(frm, cdt, cdn);
    }
});

function calculate_amount(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    if (row.quantity && row.rate) {
        let amount = flt(row.quantity) * flt(row.rate);
        frappe.model.set_value(cdt, cdn, 'amount', amount);
    } else {
        frappe.model.set_value(cdt, cdn, 'amount', 0);
    }
} 