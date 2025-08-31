frappe.ui.form.on('Delivery Note Item', {
    item: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.item) {
            // Get the customer from the parent Delivery Note
            let customer = null;
            if (frm.doc.parent) {
                let delivery_note = frappe.get_doc(frm.doc.parenttype, frm.doc.parent);
                if (delivery_note && delivery_note.customer) {
                    customer = delivery_note.customer;
                }
            }
            
            // Check if inventory.pricing is available
            if (typeof inventory !== 'undefined' && inventory.pricing) {
                // Use the pricing utility to get the price
                inventory.pricing.get_item_price(row.item, true, customer, null, function(rate, price_list) {
                    frappe.model.set_value(cdt, cdn, 'rate', rate);
                    if (price_list) {
                        let message = `Price applied from Price List: ${price_list}`;
                        if (customer) {
                            message += ` for customer ${customer}`;
                        }
                        frappe.msgprint(message);
                    } else if (rate > 0) {
                        frappe.msgprint("No price list rate found. Applied estimated selling price.");
                    }
                });
            } else {
                // Fallback to basic selling price functionality
                if (typeof get_basic_selling_price === 'function') {
                    get_basic_selling_price(row.item, customer, function(rate, price_source) {
                        if(rate > 0) {
                            frappe.model.set_value(cdt, cdn, "rate", rate);
                            
                            let message = "";
                            switch(price_source) {
                                case "customer-specific":
                                    message = `Applied customer-specific price: ${rate} for ${customer}`;
                                    break;
                                case "default-selling":
                                    message = `Applied default selling price: ${rate}`;
                                    break;
                                case "default-both":
                                    message = `Applied default price: ${rate}`;
                                    break;
                                case "general":
                                    message = `Applied general selling price: ${rate}`;
                                    break;
                                case "valuation":
                                    message = `Applied valuation-based price (with markup): ${rate}`;
                                    break;
                                default:
                                    message = `Applied price: ${rate}`;
                            }
                            frappe.msgprint(message);
                        } else {
                            frappe.msgprint("No price found for this item. Please enter the rate manually.");
                        }
                    });
                } else {
                    frappe.msgprint("Price retrieval function not found. Please enter the rate manually.");
                }
            }
        }
    },
    
    quantity: function(frm, cdt, cdn) {
        calculate_amount(frm, cdt, cdn);
    },
    
    rate: function(frm, cdt, cdn) {
        calculate_amount(frm, cdt, cdn);
    },
    
    amount: function(frm, cdt, cdn) {
        update_total_amount(frm);
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

function update_total_amount(frm) {
    // Calculate total amount from all items
    let total_amount = 0;
    
    // Get parent document (Delivery Note)
    let parent = frappe.get_doc(frm.doc.doctype, frm.doc.parent);
    
    if (parent && parent.items) {
        parent.items.forEach(function(item) {
            total_amount += flt(item.amount);
        });
        
        // Update parent's total_amount field
        frappe.model.set_value(parent.doctype, parent.name, 'total_amount', total_amount);
    }
} 