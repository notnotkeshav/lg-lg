frappe.query_reports["Regional Report"] = {
	"filters": [
		{
			"fieldname": "year",
			"label": __("Year"),
			"fieldtype": "Select",
			"options": ["", "2023", "2024", "2025", "2026"],
			"default": frappe.datetime.get_today().split("-")[0]
		},
		{
			"fieldname": "month",
			"label": __("Month"),
			"fieldtype": "Select",
			"options": ["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
		},
		{
			"fieldname": "region",
			"label": __("Region"),
			"fieldtype": "Link",
			"options": "Region Master",
			"get_query": function() {
				return {
					filters: [
						["Region Master", "name", "not in", ["East", "North"]]
					]
				};
			}
		},

		{
			"fieldname": "asm",
			"label": __("Branch Head (ASM)"),
			"fieldtype": "Link",
			"options": "User"
		}
	]
};
