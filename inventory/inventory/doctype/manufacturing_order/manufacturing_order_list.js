frappe.listview_settings['Manufacturing Order'] = {
    add_fields: ["status"],
    get_indicator: function(doc) {
        if (doc.status === "Draft") {
            return [__("Draft"), "gray", "status,=,Draft"];
        } else if (doc.status === "In Process") {
            return [__("In Process"), "orange", "status,=,In Process"];
        } else if (doc.status === "Completed") {
            return [__("Completed"), "green", "status,=,Completed"];
        } else if (doc.status === "Cancelled") {
            return [__("Cancelled"), "red", "status,=,Cancelled"];
        }
    },
    onload: function(listview) {
        listview.page.add_action_item(__('Start Production'), function() {
            const selected = listview.get_checked_items();
            if (selected.length > 0) {
                frappe.call({
                    method: 'inventory.inventory.doctype.manufacturing_order.manufacturing_order.start_production_for_selected',
                    args: {
                        manufacturing_orders: selected.map(s => s.name)
                    },
                    callback: function(r) {
                        if (!r.exc) {
                            listview.refresh();
                            frappe.show_alert({
                                message: __('Production started for selected orders'),
                                indicator: 'green'
                            });
                        }
                    }
                });
            } else {
                frappe.msgprint(__('Please select at least one Manufacturing Order'));
            }
        });

        listview.page.add_action_item(__('Complete Production'), function() {
            const selected = listview.get_checked_items();
            if (selected.length > 0) {
                frappe.call({
                    method: 'inventory.inventory.doctype.manufacturing_order.manufacturing_order.complete_production_for_selected',
                    args: {
                        manufacturing_orders: selected.map(s => s.name)
                    },
                    callback: function(r) {
                        if (!r.exc) {
                            listview.refresh();
                            frappe.show_alert({
                                message: __('Production completed for selected orders'),
                                indicator: 'green'
                            });
                        }
                    }
                });
            } else {
                frappe.msgprint(__('Please select at least one Manufacturing Order'));
            }
        });
    }
}; 