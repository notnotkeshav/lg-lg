// Copyright (c) 2024, extension and contributors
// For license information, please see license.txt

frappe.query_reports["Pipeline Report 1"] = {
	"filters": [
		{
            fieldname: "customer",
            label: __("Customer Name"),
            fieldtype: "Link",
            options: "CRM Organization",
            reqd: 0
        },
		// {
        //     fieldname: "year",
        //     label: __("Year"),
        //     fieldtype: "Select",
		// 	options: ["","2024","2025"],
        //     reqd: 0
        // }
        {
            fieldname: "industry",
            label: __("Industry"),
            fieldtype: "Link",
            options: "CRM Industry",
            reqd:0
        },
        {
            fieldname: "region",
            label: __("Region"),
            fieldtype: "Link",
            options: "Region Master",
            reqd:0
        },
        {
            fieldname: "branch",
            label: __("Branch"),
            fieldtype: "Link",
            options: "Region Branches",
            reqd:0
        },
		{
            fieldname: "payment_frequency",
            label: __("Payment Frequency"),
            fieldtype: "Select",
            options: ["","Monthly", "Quarterly", "Semi-Annually", "Annually"],
            reqd: 0
        }
        // {
        //     fieldname: "branch_head",
        //     label: __("Branch Head"),
        //     fieldtype: "data",
        //     // options: "Region Branches",
        //     reqd:0
        // }
	]
};
