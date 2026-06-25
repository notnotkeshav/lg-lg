// Copyright (c) 2025, extension and contributors
// For license information, please see license.txt

frappe.ui.form.on("Invoice", {
    posting_date: function (frm) {
        if (frm.doc.pay_term && frm.doc.posting_date) {
            frm.save().then(() => {
                frappe.call({
                    method: "lg.lg.doctype.invoice.invoice.update_due_dates_from_posting",
                    args: { invoice_id: frm.doc.name },
                    callback: function (r) {
                        if (r.message) {
                            frappe.msgprint(r.message.message);
                            frm.reload_doc();
                        }
                    }
                });
            });
        }
    }
});


frappe.ui.form.on("Invoice Payment Term", {
    amount_received: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.amount_received) {
            // Update outstanding for this row
            let outstanding = row.portion_amount - row.amount_received;
            frappe.model.set_value(cdt, cdn, "outstanding_as_per_portion", outstanding);
        }

        // --- Now update parent Invoice fields ---
        let total_paid = 0;
        (frm.doc.invoice_payment_term || []).forEach(term => {
            total_paid += term.amount_received || 0;
        });

        // Update parent totals
        frm.set_value("total_paid", total_paid);
        let total_outstanding = (frm.doc.amount_invoiced || 0) - total_paid;
        frm.set_value("total_outstanding", total_outstanding);

        // Update parent status
        if ((frm.doc.amount_invoiced || 0) === total_paid) {
            frm.set_value("status", "Paid");
        } else {
            frm.set_value("status", "Partially Paid");
        }

        frm.refresh_fields(["total_paid", "total_outstanding", "status"]);
    }
});
