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
		const user = frappe.session.user
		const billing_allowed_users = [
			"Administrator",
			"indra.kumar@lgepartner.com"
		];

		const payment_allowed_users = [
			"Administrator",
			"dheeraj.chauhan@lge.com" // Replace with Dheeraj's actual login email
		];


		if (billing_allowed_users.includes(user)) {
			if (!listview.upload_billing_btn) {
				listview.upload_billing_btn = listview.page.add_inner_button(
					__("Upload Billing"),
					() => upload_billing(listview)
				);
			}
			if (!listview.upload_amc_billing_btn) {
				listview.upload_amc_billing_btn = listview.page.add_inner_button(
					__("Upload AMC Billing"),
					() => upload_amc_billing(listview)
				);
			}
		}

		if (payment_allowed_users.includes(user)) {
			if (!listview.upload_payment_btn) {
				listview.upload_payment_btn = listview.page.add_inner_button(
					__("Upload Payment"),
					() => upload_payment(listview)
				);
			}
		}
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

function upload_billing(listview) {
	new frappe.ui.FileUploader({
		doctype: "CRM Contract",
		restrictions: { allowed_file_types: [".xlsx"] },
		make_attachments_public: false,
		on_success(file) {
			frappe.call({
				method: "lg.lg.doctype.crm_contract.crm_contract.upload_billing",
				args: { file_url: file.file_url },
				freeze: true,
				freeze_message: __("Updating billing..."),
				callback({ message }) {
					const { updated, errors } = message;
					let html = `<p>${__("{0} contract(s) updated", [updated.length])}</p>`;
					if (errors.length) {
						html += `<p class="text-danger">${__("{0} row(s) skipped", [errors.length])}:</p><ul>${errors.map(e => `<li>${frappe.utils.escape_html(e)}</li>`).join("")}</ul>`;
					}
					frappe.msgprint({ title: __("Upload Billing"), message: html, indicator: errors.length ? "orange" : "green" });
					listview.refresh();
				},
			});
		},
	});
}

// AMC Raw data sheet (.xlsb/.xlsx): preview first (dry run), save only after confirmation
function upload_amc_billing(listview) {
	new frappe.ui.FileUploader({
		doctype: "CRM Contract",
		restrictions: { allowed_file_types: [".xlsb", ".xlsx"] },
		make_attachments_public: false,
		on_success(file) {
			const run = (dry_run) => frappe.call({
				method: "lg.lg.doctype.crm_contract.crm_contract.upload_amc_billing",
				args: { file_url: file.file_url, dry_run },
				freeze: true,
				freeze_message: dry_run ? __("Checking billing...") : __("Updating billing..."),
				callback({ message }) {
					const { updated, errors } = message;
					const list = (items) => `<ul>${items.slice(0, 200).map(e => `<li>${frappe.utils.escape_html(e)}</li>`).join("")}</ul>`
						+ (items.length > 200 ? `<p>${__("... and {0} more", [items.length - 200])}</p>` : "");
					let html = `<p>${__("{0} contract(s) {1}", [updated.length, dry_run ? __("will be updated") : __("updated")])}</p>`;
					if (updated.length) html += list(updated);
					if (errors.length) html += `<p class="text-danger">${__("{0} row(s) skipped", [errors.length])}:</p>${list(errors)}`;
					if (dry_run) {
						frappe.confirm(html + `<p><b>${__("Apply these changes?")}</b></p>`, () => run(0));
					} else {
						frappe.msgprint({ title: __("Upload AMC Billing"), message: html, indicator: errors.length ? "orange" : "green" });
						listview.refresh();
					}
				},
			});
			run(1);
		},
	});
}

function upload_payment(listview) {
	new frappe.ui.FileUploader({
		doctype: "CRM Contract",
		restrictions: { allowed_file_types: [".xlsx"] },
		make_attachments_public: false,
		on_success(file) {
			frappe.call({
				method: "lg.lg.doctype.crm_contract.crm_contract.upload_payment",
				args: { file_url: file.file_url },
				freeze: true,
				freeze_message: __("Updating payments..."),
				callback({ message }) {
					const { updated, errors } = message;
					let html = `<p>${__("{0} contract(s) updated", [updated.length])}</p>`;
					if (errors.length) {
						html += `<p class="text-danger">${__("{0} row(s) skipped", [errors.length])}:</p><ul>${errors.map(e => `<li>${frappe.utils.escape_html(e)}</li>`).join("")}</ul>`;
					}
					frappe.msgprint({ title: __("Upload Payment"), message: html, indicator: errors.length ? "orange" : "green" });
					listview.refresh();
				},
			});
		},
	});
}
