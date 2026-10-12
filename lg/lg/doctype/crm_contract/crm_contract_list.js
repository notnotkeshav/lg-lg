// CRM Contract list: Customer Name (title field) | Region | Branch | Contract Status.
// The middle columns come from List View Settings. Replaces the "Hide Add Contract
// Button" and "Create Update Invoice" Client Scripts, which are kept disabled in
// fixtures/client_script.json.
frappe.listview_settings["CRM Contract"] = Object.assign(frappe.listview_settings["CRM Contract"] || {}, {
	// customer_name is the title field, so Frappe would add the record name as an
	// extra "ID" column after the configured ones
	hide_name_column: true,

	refresh(listview) {
		// contracts are created from quotations, not from the list
		listview.page.clear_primary_action();
	},
});

// Give Customer Name more width than the other columns (default flex is 2)
if (!document.getElementById("crm-contract-list-style")) {
	$(`<style id="crm-contract-list-style">
		.page-container[data-page-route="List/CRM Contract/List"] .list-subject {
			flex: 4;
		}
	</style>`).appendTo("head");
}
