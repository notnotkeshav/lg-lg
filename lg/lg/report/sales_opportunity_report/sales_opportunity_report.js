// Copyright (c) 2025, extension and contributors
// For license information, please see license.txt

frappe.query_reports["Sales Opportunity Report"] = {
	"filters": [

        {
            fieldname: "expiry_date",
            label: __("Expiry Date (<=)"),
            fieldtype: "Date",
            default: frappe.datetime.now_date()
        },
        {
            fieldname: "branch",
            label: __("Branch"),
            fieldtype: "Link",
            options: "Region Branches"
        },
        {
            fieldname: "region",
            label: __("Region"),
            fieldtype: "Link",
            options: "Region Master"
        }
    ],

    // Optional: format days_to_expiry with colors
    "formatter": function(value, row, column, data, default_formatter) {
        if (column.fieldname === "days_to_expiry" && data) {
            let color = "black";

            if (value < 0) {
                color = "red";   // expired
            } else if (value <= 30) {
                color = "orange"; // expiring soon
            } else {
                color = "green"; // safe
            }

            value = default_formatter(value, row, column, data);
            return `<span style="color:${color}; font-weight:bold">${value}</span>`;
        }

        return default_formatter(value, row, column, data);
    }
};

