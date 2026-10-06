// Copyright (c) 2026, extension and contributors
// For license information, please see license.txt

const MONTHS = [
	"January", "February", "March", "April", "May", "June",
	"July", "August", "September", "October", "November", "December",
];

frappe.query_reports["Active Contract Net Revenue"] = {
	filters: [
		{
			fieldname: "month",
			label: __("Month"),
			fieldtype: "Select",
			options: MONTHS,
			default: MONTHS[moment().month()],
			reqd: 1,
		},
		{
			fieldname: "year",
			label: __("Year"),
			fieldtype: "Select",
			// 3 years back to 1 year ahead
			options: [-3, -2, -1, 0, 1].map((offset) => String(moment().year() + offset)),
			default: String(moment().year()),
			reqd: 1,
		},
		{
			fieldname: "customer",
			label: __("Customer"),
			fieldtype: "Link",
			options: "CRM Organization",
		},
		{
			fieldname: "region",
			label: __("Region"),
			fieldtype: "Link",
			options: "Region Master",
		},
		{
			fieldname: "branch",
			label: __("Branch"),
			fieldtype: "Link",
			options: "Region Branches",
		},
	],
};
