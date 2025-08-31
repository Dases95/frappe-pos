frappe.ui.form.on('Purchase Receipt Item', {
    item: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.item) {
            // Get batch tracking info
            frappe.db.get_value('Item', row.item, ['batch_tracking'], (r) => {
                if (r) {
                    if (r.batch_tracking) {
                        frappe.model.set_value(cdt, cdn, 'has_batch', r.batch_tracking);
                    } else {
                        frappe.model.set_value(cdt, cdn, 'has_batch', 0);
                    }
                }
            });
            
            // Get supplier from parent document if available
            let supplier = null;
            if (frm.doc.parenttype === "Purchase Receipt") {
                // Try to get the parent document
                let parent_form = cur_frm;
                if (parent_form && parent_form.doc && parent_form.doc.supplier) {
                    supplier = parent_form.doc.supplier;
                }
                
                // If we have supplier and inventory.pricing is available, get the price
                if (supplier && typeof inventory !== 'undefined' && inventory.pricing) {
                    inventory.pricing.get_item_price(row.item, false, null, supplier, function(rate, price_list) {
                        if (rate > 0) {
                            frappe.model.set_value(cdt, cdn, 'rate', rate);
                            
                            let message = `Price applied: ${rate}`;
                            if (price_list) {
                                message = `Price applied from Price List: ${price_list}`;
                                if (supplier) {
                                    message += ` for supplier ${supplier}`;
                                }
                            }
                            frappe.msgprint(message);
                        }
                    });
                } else if (supplier) {
                    // Fallback to direct item price lookup
                    frappe.call({
                        method: "frappe.client.get_list",
                        args: {
                            doctype: "Item Price",
                            filters: {
                                "item_code": row.item,
                                "buying": 1,
                                "supplier": supplier
                            },
                            fields: ["price_list_rate", "price_list"],
                            order_by: "modified desc",
                            limit: 1
                        },
                        callback: function(r) {
                            if (r.message && r.message.length > 0) {
                                frappe.model.set_value(cdt, cdn, 'rate', r.message[0].price_list_rate);
                                frappe.msgprint(`Price applied from Price List: ${r.message[0].price_list} for supplier ${supplier}`);
                            } else {
                                // Try general price
                                frappe.call({
                                    method: "frappe.client.get_list",
                                    args: {
                                        doctype: "Item Price",
                                        filters: {
                                            "item_code": row.item,
                                            "buying": 1,
                                            "supplier": ["in", ["", null]]
                                        },
                                        fields: ["price_list_rate", "price_list"],
                                        order_by: "modified desc",
                                        limit: 1
                                    },
                                    callback: function(r) {
                                        if (r.message && r.message.length > 0) {
                                            frappe.model.set_value(cdt, cdn, 'rate', r.message[0].price_list_rate);
                                            frappe.msgprint(`Price applied from general Price List: ${r.message[0].price_list}`);
                                        } else {
                                            // Last resort: Try item's last purchase or valuation rate
                                            frappe.db.get_value('Item', row.item, ['last_purchase_rate', 'valuation_rate'], (item_values) => {
                                                if (item_values) {
                                                    let rate = item_values.last_purchase_rate || item_values.valuation_rate || 0;
                                                    if (rate > 0) {
                                                        frappe.model.set_value(cdt, cdn, 'rate', rate);
                                                        frappe.msgprint(`Applied historical purchase price as no price list was found.`);
                                                    } else {
                                                        frappe.msgprint(`No price found for this item. Please enter the rate manually.`);
                                                    }
                                                }
                                            });
                                        }
                                    }
                                });
                            }
                        }
                    });
                }
            } else {
                // If no supplier context, get default rates from item
                frappe.db.get_value('Item', row.item, ['last_purchase_rate', 'valuation_rate'], (r) => {
                    if (r) {
                        let default_rate = r.last_purchase_rate || r.valuation_rate || 0;
                        if (default_rate > 0) {
                            frappe.model.set_value(cdt, cdn, 'rate', default_rate);
                        }
                    }
                });
            }
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