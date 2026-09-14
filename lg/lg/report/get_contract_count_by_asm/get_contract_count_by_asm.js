function get_year_options() {
	const current_year = new Date().getFullYear();

	const years = [];

	// Previous 2 years
	// Current year
	// Next 2 years
	for (
			let year = current_year - 2;
			year <= current_year + 2;
			year++
	) {
			years.push(String(year));
	}

	return years.join("\n");
}


frappe.query_reports["Get Contract Count By ASM"] = {

	filters: [

			// =====================================================
			// REGION
			// =====================================================

			{
					fieldname: "region",
					label: __("Region"),
					fieldtype: "Link",
					options: "Region"
			},

			// =====================================================
			// Branch
			// =====================================================

			{
					fieldname: "branch",
					label: __("Branch"),
					fieldtype: "Link",
					options: "branch"
			},

			// =====================================================
			// ASM
			// =====================================================

			{
					fieldname: "asm",
					label: __("ASM"),
					fieldtype: "Link",
					options: "User"
			},

			// =====================================================
			// YEAR
			// =====================================================

			{
					fieldname: "year",
					label: __("Year"),
					fieldtype: "Select",
					options: get_year_options(),
					default: String(new Date().getFullYear()),
					reqd: 1
			},

			// =====================================================
			// CONTRACT TYPE
			// =====================================================

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

			// =====================================================
			// GROUP BY
			// =====================================================

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