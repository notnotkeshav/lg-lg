// CRM Deal form: probability banner and total HP.
//
// Replaces the "Update Probability on deal status update", "Deal child product
// details" and "fetch total hp" Client Scripts. Never call set_value from
// refresh/onload here: any value that differs from the saved one marks every
// opened deal as "Not Saved". probability and total_hp are recomputed on the
// server in CRMDeal.validate(), so the form only previews them while editing.

// Keep in sync with STATUS_PROBABILITY in lg/lg/doctype/crm_deal/crm_deal.py
const DEAL_STATUS_PROBABILITY = {
	"Qualification": 10,
	"Proposal/Quotation": 40,
	"Negotiation": 60,
	"Spec-In": 80,
	"Ready to Close": 80,
	"Won/Award": 100,
};

frappe.ui.form.on("CRM Deal", {
	refresh(frm) {
		render_probability_banner(frm, frm.doc.probability);
	},

	status(frm) {
		const probability = DEAL_STATUS_PROBABILITY[frm.doc.status] || 0;
		set_if_changed(frm, "probability", probability);
		render_probability_banner(frm, probability);
	},

	product_details_remove(frm) {
		update_total_hp(frm);
	},
});

frappe.ui.form.on("Product Details", {
	hp(frm) {
		update_total_hp(frm);
	},
});

function set_if_changed(frm, fieldname, value) {
	if (frm.doc[fieldname] !== value) {
		frm.set_value(fieldname, value);
	}
}

// Same formula as CRMDeal.set_total_hp()
function update_total_hp(frm) {
	const total = (frm.doc.product_details || []).reduce((sum, row) => sum + flt(row.hp), 0);
	set_if_changed(frm, "total_hp", cint(total));
}

function render_probability_banner(frm, value) {
	const field = frm.fields_dict.custom_probability_progress;
	if (!field || frm.doc.status === "Sales") return;

	const val = cint(value);
	const color =
		val >= 100 ? "hsl(250,50%,50%)" :
		val >= 80 ? "hsl(200,50%,50%)" :
		val >= 60 ? "hsl(150,50%,50%)" :
		val >= 40 ? "hsl(30,80%,50%)" :
		val > 0 ? "hsl(0,50%,50%)" :
		"#333";

	// changes only the field's display, not the document, so it never dirties the form
	frm.set_df_property("custom_probability_progress", "options", `
		<div style="width: 100%; padding: 20px 10px;">
			<div>${__("Probability")}: ${val}%</div>
			<div style="height: 20px; width: 100%; border: 1px solid #ddd; border-radius: 50px;">
				<div style="height: 100%; width: ${val}%; background: ${color}; border-radius: 50px;"></div>
			</div>
		</div>
	`);
}
