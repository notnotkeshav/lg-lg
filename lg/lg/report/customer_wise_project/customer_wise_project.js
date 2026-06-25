// Copyright (c) 2025, extension and contributors
// For license information, please see license.txt

// your_app/your_app/report/project_summary_report/project_summary_report.js

frappe.query_reports["Customer Wise Project"] = {
    "filters": [
        {
            "fieldname": "customer",
            "label": "Customer",
            "fieldtype": "Link",
            "options": "CRM Organization",
            "default": "",
        },
        {
            "fieldname": "project",
            "label": "Project",
            "fieldtype": "Link",
			"options":"Project",
            "default": "",
        },
        {
            "fieldname": "status",
            "label": "Project Status",
            "fieldtype": "Select",
            "options": "\nIn Warranty\nOUT Warranty\nAMC Active\nAMC Expired",
            "default": "",
        },
		{
            "fieldname": "vertical",
            "label": "Vertical",
            "fieldtype": "Link",
			"options": "CRM Industry",
            "default": "",
        },

        {
            "fieldname": "region",
            "label": "Customer Region",
            "fieldtype": "Link",
			"options": "Region Master",
            "default": "",
        }
    ]
};
