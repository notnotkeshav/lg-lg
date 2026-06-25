// Copyright (c) 2024, extension and contributors
// For license information, please see license.txt

frappe.query_reports["Pipeline Report 3"] = {
	"filters": [
		{
            fieldname: "customer",
            label: __("Customer Name"),
            fieldtype: "Link",
            options: "CRM Organization",
            reqd: 0
        },
		{
            fieldname: "payment_frequency",
            label: __("Payment Frequency"),
            fieldtype: "Select",
            options: ["","Monthly", "Quarterly", "Semi-Annually", "Annually"],
            reqd: 0
        }
		// {
        //     fieldname: "year",
        //     label: __("Year"),
        //     fieldtype: "Select",
		// 	options: ["","2024","2025"],
        //     reqd: 0
        // }

	]
};
