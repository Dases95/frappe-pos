frappe.ui.form.on('Stock Entry Item', {
    item: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.item) {
            frappe.db.get_value('Item', row.item, ['batch_tracking', 'valuation_rate'], (r) => {
                if (r) {
                    if (r.batch_tracking) {
                        frappe.model.set_value(cdt, cdn, 'has_batch', r.batch_tracking);
                    } else {
                        frappe.model.set_value(cdt, cdn, 'has_batch', 0);
                    }
                    
                    // Set default rate if available and not already set
                    if (r.valuation_rate && !row.rate) {
                        frappe.model.set_value(cdt, cdn, 'rate', r.valuation_rate);
                    }
                }
            });
        } else {
            frappe.model.set_value(cdt, cdn, 'has_batch', 0);
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