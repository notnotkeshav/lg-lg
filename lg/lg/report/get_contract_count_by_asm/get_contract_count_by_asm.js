function get_year_options() {
	const current_year = new Date().getFullYear();

	const years = [""];
	
	for (let year = current_year - 2; year <= current_year + 3; year++) {
			years.push(String(year));
	}

	return years.join("\n");
}

frappe.query_reports["Get Contract Count By ASM"] = {
	filters: [
		{
			fieldname: "region",
			label: __("Region"),
			fieldtype: "Link",
			options: "Region"
		},
		{
			fieldname: "branch",
			label: __("Branch"),
			fieldtype: "Link",
			options: "Branch"
		},
		{
			fieldname: "asm",
			label: __("ASM"),
			fieldtype: "Link",
			options: "User"
		},
		{
			fieldname: "year",
			label: __("Year"),
			fieldtype: "Select",
			options: get_year_options()
		},
		{
			fieldname: "deal_type",
			label: __("Contract Type"),
			fieldtype: "Select",
			options: [
				"",
				"AMC Renewal",
				"Warranty AMC Conversion",
				"Lost Warranty Conversion",
				"Lost AMC Conversion"
			].join("\n")
		},
		{
			fieldname: "group_by",
			label: __("Group By"),
			fieldtype: "Select",
			options: [
				"Monthly",
				"Quarterly",
				"Annually"
			].join("\n"),
			default: "Monthly",
			reqd: 1
		}
	]
};