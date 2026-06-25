// Copyright (c) 2026, extension and contributors
// For license information, please see license.txt

frappe.query_reports["Contract Status Report"] = {
	"filters": [
        {
            "fieldname": "region",
            "label": "Region",
            "fieldtype": "Link",
            "options": "Region Master"
        },
        {
            "fieldname": "branch",
            "label": "Branch",
            "fieldtype": "Link",
            "options": "Region Branches"
        },
        {
            "fieldname": "asm_name",
            "label": "ASM Name",
            "fieldtype": "Data"
        },
		{
			"fieldname": "status",
			"label": "Status",
			"fieldtype": "Select",
			"options": ["Active", "Expired"],
			"default": "Expired", // By default Expired select rahega
			"reqd": 1
		}
    ]
};
