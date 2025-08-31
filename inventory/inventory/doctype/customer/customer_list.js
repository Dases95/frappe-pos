frappe.listview_settings['Customer'] = {
    // Add indicators to customers
    get_indicator: function(doc) {
        if (doc.status === "Active") {
            return [__("Active"), "green", "status,=,Active"];
        } else if (doc.status === "Inactive") {
            return [__("Inactive"), "red", "status,=,Inactive"];
        }
        return [__(doc.status), "gray", "status,=," + doc.status];
    },
    
    // Add quick filters and buttons when list loads
    onload: function(listview) {
        // Add quick filter buttons at the top
        listview.page.add_inner_button(__('Active Customers'), function() {
            listview.filter_area.add([[listview.doctype, "status", "=", "Active"]]);
        }, __('Quick Filters'));
        
        listview.page.add_inner_button(__('Inactive Customers'), function() {
            listview.filter_area.add([[listview.doctype, "status", "=", "Inactive"]]);
        }, __('Quick Filters'));
        
        listview.page.add_inner_button(__('Retailers'), function() {
            listview.filter_area.add([[listview.doctype, "customer_type", "=", "Retailer"]]);
        }, __('Customer Type'));
        
        listview.page.add_inner_button(__('Wholesalers'), function() {
            listview.filter_area.add([[listview.doctype, "customer_type", "=", "Wholesaler"]]);
        }, __('Customer Type'));
        
        listview.page.add_inner_button(__('Distributors'), function() {
            listview.filter_area.add([[listview.doctype, "customer_type", "=", "Distributor"]]);
        }, __('Customer Type'));
        
        // Add a filter by wilaya button
        listview.page.add_inner_button(__('Filter by Wilaya'), function() {
            let d = new frappe.ui.Dialog({
                title: __('Select Wilaya'),
                fields: [
                    {
                        label: __('Wilaya'),
                        fieldname: 'wilaya',
                        fieldtype: 'Link',
                        options: 'Wilaya',
                        reqd: 1
                    }
                ],
                primary_action_label: __('Filter'),
                primary_action: function(values) {
                    listview.filter_area.add([[listview.doctype, "wilaya", "=", values.wilaya]]);
                    d.hide();
                }
            });
            d.show();
        }, __('Geographic Filters'));
        
        // Add a filter by commune button
        listview.page.add_inner_button(__('Filter by Commune'), function() {
            let d = new frappe.ui.Dialog({
                title: __('Select Commune'),
                fields: [
                    {
                        label: __('Wilaya'),
                        fieldname: 'wilaya',
                        fieldtype: 'Link',
                        options: 'Wilaya'
                    },
                    {
                        label: __('Commune'),
                        fieldname: 'commune',
                        fieldtype: 'Link',
                        options: 'Commune',
                        reqd: 1,
                        get_query: function() {
                            let wilaya = d.get_value('wilaya');
                            if (wilaya) {
                                return {
                                    filters: {
                                        'wilaya': wilaya
                                    }
                                };
                            }
                        }
                    }
                ],
                primary_action_label: __('Filter'),
                primary_action: function(values) {
                    listview.filter_area.add([[listview.doctype, "commune", "=", values.commune]]);
                    d.hide();
                }
            });
            d.show();
        }, __('Geographic Filters'));
        
        // Add Export action
        listview.page.add_inner_button(__('Export Customers'), function() {
            frappe.set_route('List', 'Customer', 'Report');
        }, __('Actions'));
        
        // Add Print action
        listview.page.add_inner_button(__('Print List'), function() {
            frappe.route_options = {
                name: listview.get_checked_items().map(function(doc) {
                    return doc.name;
                })
            };
            frappe.set_route('print', 'Customer');
        }, __('Actions'));
    },
    
    // Custom formatters for fields in list view
    formatters: {
        customer_type: function(value, df, doc) {
            let colors = {
                "Retailer": "#5e64ff",
                "Wholesaler": "#743ee2",
                "Distributor": "#ff5858"
            };
            let color = colors[value] || "#7578f6";
            return `<span class="indicator-pill" style="background-color: ${color}; color: white; font-weight: 500; padding: 3px 8px; border-radius: 10px;">${value}</span>`;
        },
        
        contact_number: function(value) {
            if (!value) return '';
            return `<a href="tel:${value}" title="${__('Call')}" style="text-decoration: none;">
                <span><i class="fa fa-phone" style="margin-right: 5px; color: #5e64ff;"></i>${value}</span>
            </a>`;
        },
        
        email: function(value) {
            if (!value) return '';
            return `<a href="mailto:${value}" title="${__('Send Email')}" style="text-decoration: none;">
                <span><i class="fa fa-envelope" style="margin-right: 5px; color: #5e64ff;"></i>${value}</span>
            </a>`;
        }
    },
    
    // Add buttons for each row in the list
    button: {
        show: function(doc) {
            return doc.status === 'Active';
        },
        get_label: function() {
            return __('View');
        },
        get_description: function(doc) {
            return __('View {0}', [doc.customer_name]);
        },
        action: function(doc) {
            frappe.set_route('Form', 'Customer', doc.name);
        }
    }
}; 