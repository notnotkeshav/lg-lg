// CRM Quotation list: show Status as a colored pill. Colors come from the "color"
// field of the CRM Quotation Status master, so they can be changed from the UI.
// The list columns themselves are set by the "Hide Add Quote button" Client Script.
const crm_quotation_status_colors = {};

frappe.db
	.get_list("CRM Quotation Status", { fields: ["name", "color"], limit: 0 })
	.then((rows) => {
		rows.forEach((row) => (crm_quotation_status_colors[row.name] = row.color));
		// re-render rows drawn before the colors arrived
		if (window.cur_list && cur_list.doctype === "CRM Quotation") cur_list.render();
	});

frappe.listview_settings["CRM Quotation"] = Object.assign(frappe.listview_settings["CRM Quotation"] || {}, {
	formatters: Object.assign((frappe.listview_settings["CRM Quotation"] || {}).formatters || {}, {
		status(value) {
			if (!value) return "";
			const color = crm_quotation_status_colors[value] || "var(--gray-500)";
			const label = frappe.utils.escape_html(__(value));
			return `<span class="filterable crm-quotation-status"
				data-filter="status,=,${frappe.utils.escape_html(value)}"
				style="--status-color: ${frappe.utils.escape_html(color)}"
				title="${label}">${label}</span>`;
		},
	}),
});

if (!document.getElementById("crm-quotation-status-style")) {
	$(`<style id="crm-quotation-status-style">
		.crm-quotation-status {
			display: inline-flex;
			align-items: center;
			gap: 6px;
			max-width: 100%;
			padding: 2px 10px;
			border-radius: 999px;
			font-size: var(--text-xs);
			font-weight: 500;
			color: var(--text-color);
			background: color-mix(in srgb, var(--status-color) 20%, transparent);
			overflow: hidden;
			text-overflow: ellipsis;
			white-space: nowrap;
		}
		.crm-quotation-status::before {
			content: "";
			flex: none;
			width: 8px;
			height: 8px;
			border-radius: 50%;
			background: var(--status-color);
		}
	</style>`).appendTo("head");
}
