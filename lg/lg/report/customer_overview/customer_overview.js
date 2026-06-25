// Copyright (c) 2025, extension and contributors
// For license information, please see license.txt

frappe.query_reports["Customer Overview"] = {
    "filters": [
        // {
        //     "fieldname": "from_date",
        //     "label": "From Date",
        //     "fieldtype": "Date",
        //     "default": "2025-04-01"
        // },
        // {
        //     "fieldname": "to_date",
        //     "label": "To Date",
        //     "fieldtype": "Date",
        //     "default": "2026-03-31"
        // },
        {
            "fieldname": "customer",
            "label": "Customer",
            "fieldtype": "Link",
            "options": "CRM Organization"
        }
    ]
};
