// Merge with other Project list scripts instead of replacing them
frappe.listview_settings["Project"] = Object.assign(frappe.listview_settings["Project"] || {}, {
	// project_name is the title field and the record name, so the extra ID column
	// Frappe adds after the List View Settings columns only repeats the first one
	hide_name_column: true,
});
