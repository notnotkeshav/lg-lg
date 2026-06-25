// Copyright (c) 2025, extension and contributors
// For license information, please see license.txt


frappe.query_reports["To be Expired"] = {
    filters: [
        {
            fieldname: "period_type",
            label: "Select Period Type",
            fieldtype: "Select",
            options: ["Days", "Months"],
            default: "Days",
            reqd: 1,
            on_change: function (report) {
                const periodType = frappe.query_report.get_filter_value('period_type');

                // Show/hide filters dynamically
                if (periodType === "Days") {
                    frappe.query_report.toggle_filter_display('days_value', true);
                    frappe.query_report.toggle_filter_display('months_value', false);
                } else {
                    frappe.query_report.toggle_filter_display('days_value', false);
                    frappe.query_report.toggle_filter_display('months_value', true);
                }
            }
        },
        {
            fieldname: "days_value",
            label: "Number of Days",
            fieldtype: "Int",
            default: 30
        },
        {
            fieldname: "months_value",
            label: "Number of Months",
            fieldtype: "Int",
            default: 1
        }
    ],
    
    onload: function(report) {
        // Initial state
        frappe.query_report.toggle_filter_display('months_value', false);
    }
};
