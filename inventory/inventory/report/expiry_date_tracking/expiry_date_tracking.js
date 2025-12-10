frappe.query_reports["Expiry Date Tracking"] = {
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
            "fieldname": "status",
            "label": __("Status"),
            "fieldtype": "Select",
            "options": "\nExpired\nExpiring Soon\nWarning\nGood"
        },
        {
            "fieldname": "expiring_soon_days",
            "label": __("Expiring Soon (Days)"),
            "fieldtype": "Int",
            "default": 30
        },
        {
            "fieldname": "warning_days",
            "label": __("Warning (Days)"),
            "fieldtype": "Int",
            "default": 90
        },
        {
            "fieldname": "hide_good",
            "label": __("Hide Good Status"),
            "fieldtype": "Check",
            "default": 0
        }
    ],
    
    "formatter": function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        
        if (column.fieldname == "status") {
            if (data.status == "Expired") {
                value = "<span style='color:white; background-color:#dc3545; padding:2px 8px; border-radius:3px; font-weight:bold;'>" + value + "</span>";
            } else if (data.status == "Expiring Soon") {
                value = "<span style='color:white; background-color:#fd7e14; padding:2px 8px; border-radius:3px; font-weight:bold;'>" + value + "</span>";
            } else if (data.status == "Warning") {
                value = "<span style='color:black; background-color:#ffc107; padding:2px 8px; border-radius:3px;'>" + value + "</span>";
            } else if (data.status == "Good") {
                value = "<span style='color:white; background-color:#28a745; padding:2px 8px; border-radius:3px;'>" + value + "</span>";
            }
        }
        
        if (column.fieldname == "days_to_expiry") {
            if (data.days_to_expiry < 0) {
                value = "<span style='color:#dc3545; font-weight:bold;'>" + value + " (Expired)</span>";
            } else if (data.days_to_expiry <= 30) {
                value = "<span style='color:#fd7e14; font-weight:bold;'>" + value + "</span>";
            } else if (data.days_to_expiry <= 90) {
                value = "<span style='color:#ffc107;'>" + value + "</span>";
            }
        }
        
        if (column.fieldname == "expiry_date" && data.days_to_expiry < 0) {
            value = "<span style='color:#dc3545; font-weight:bold;'>" + value + "</span>";
        }
        
        return value;
    }
};

