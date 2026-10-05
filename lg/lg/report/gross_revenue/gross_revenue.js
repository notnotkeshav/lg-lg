// Copyright (c) 2026, extension and contributors
// For license information, please see license.txt

frappe.query_reports["Gross Revenue"] = {
	filters: [
		{
			fieldname: "as_on_date",
			label: __("As On Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{
			fieldname: "category",
			label: __("Category"),
			fieldtype: "Select",
			options: ["", "Due This Month", "Overdue", "Partially Paid"],
		},
		{
			fieldname: "chart_by",
			label: __("Chart By"),
			fieldtype: "Select",
			options: ["Ageing", "Category", "Customer", "Region", "Branch", "Due Month"],
			default: "Ageing",
		},
		{
			fieldname: "contract",
			label: __("Contract"),
			fieldtype: "Link",
			options: "CRM Contract",
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

	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (!data || data.is_total_row) return value;

		const color = (c, weight = 600) =>
			`<span style="color: var(--${c}-600); font-weight: ${weight}">${value}</span>`;

		switch (column.fieldname) {
			case "category": {
				const c = { Overdue: "red", "Partially Paid": "orange", "Due This Month": "blue" }[data.category];
				return c ? color(c) : value;
			}
			case "days_overdue":
			case "ageing": {
				// Ageing buckets: 1-30 watch, 31-60 follow up, 61-90 escalate, 90+ critical
				const days = data.days_overdue || 0;
				if (days > 90) return color("red", 700);
				if (days > 60) return color("orange");
				if (days > 30) return color("yellow");
				if (days > 0) return color("blue", 500);
				return color("green", 400);
			}
			case "outstanding":
				return data.outstanding > 0 ? color("red", 500) : value;
			case "amount_received":
				return data.amount_received > 0 ? color("green", 500) : value;
		}
		return value;
	},
};
