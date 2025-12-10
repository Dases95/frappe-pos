frappe.query_reports["Low Stock Alert"] = {
    "filters": [
        {
            "fieldname": "item",
            "label": __("Item"),
            "fieldtype": "Link",
            "options": "Item"
        },
        {
            "fieldname": "warehouse",
            "label": __("Warehouse"),
            "fieldtype": "Link",
            "options": "Warehouse"
        },
        {
            "fieldname": "show_all",
            "label": __("Show All Items"),
            "fieldtype": "Check",
            "default": 0
        }
    ],
    
    "formatter": function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        
        if (column.fieldname == "status") {
            if (data.status == "Out of Stock") {
                value = "<span style='color:white; background-color:#dc3545; padding:2px 8px; border-radius:3px;'>" + value + "</span>";
            } else if (data.status == "Low Stock") {
                value = "<span style='color:white; background-color:#fd7e14; padding:2px 8px; border-radius:3px;'>" + value + "</span>";
            } else if (data.status == "Warning") {
                value = "<span style='color:black; background-color:#ffc107; padding:2px 8px; border-radius:3px;'>" + value + "</span>";
            } else {
                value = "<span style='color:white; background-color:#28a745; padding:2px 8px; border-radius:3px;'>" + value + "</span>";
            }
        }
        
        if (column.fieldname == "shortage" && data.shortage > 0) {
            value = "<span style='color:#dc3545; font-weight:bold;'>" + value + "</span>";
        }
        
        if (column.fieldname == "days_of_stock" && data.days_of_stock !== null) {
            if (data.days_of_stock < 7) {
                value = "<span style='color:#dc3545; font-weight:bold;'>" + value + "</span>";
            } else if (data.days_of_stock < 14) {
                value = "<span style='color:#fd7e14;'>" + value + "</span>";
            }
        }
        
        return value;
    }
};

