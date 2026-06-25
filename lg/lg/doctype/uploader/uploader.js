frappe.ui.form.on('Uploader', {
    upload: function (frm) {
        console.log("Upload button clicked, type:", frm.doc.upload);

        if (frm.doc.upload === "Invoice") {
            frappe.call({
                method: "lg.lg.doctype.uploader.uploader.get_invoice_upload_data",
                freeze: true,
                freeze_message: "Fetching pending invoices...",
                callback: function (r) {
                    console.log("invoice data fetch from contract", r)
                    if (r.message && Array.isArray(r.message)) {
                        frm.clear_table("invoice_uploader");
                        r.message.forEach(row_data => {
                            let row = frm.add_child("invoice_uploader");
                            row.contract_id = row_data.contract_id;
                            row.customer = row_data.customer;
                            row.project = row_data.project;
                            row.billing_date = row_data.billing_date;
                            row.amount = row_data.amount;
                            row.bill_ship_code = row_data.bill_ship_code;
                        });
                        frm.refresh_field("invoice_uploader");
                        frappe.msgprint(__("Invoice data loaded successfully"));
                    } else {
                        frappe.msgprint(__("No matching billing schedules found"));
                    }
                }
            });
        }
        else if (frm.doc.upload === "Payment") {
            frappe.call({
                method: "lg.lg.doctype.uploader.uploader.get_payment_upload_data",
                freeze: true,
                freeze_message: "Fetching due payments...",
                args: {
                    docname: frm.doc.name
                },
                callback: function (r) {
                    console.log("Payment data fetched from Invoice:", r);
                    if (r.message && Array.isArray(r.message)) {
                        frm.clear_table("payment_uploader");
                        r.message.forEach(row_data => {
                            let row = frm.add_child("payment_uploader");
                            row.invoice_id = row_data.invoice_id;        // 🔹 from Invoice
                            row.contract_id = row_data.contract_id;      // 🔹 from amc_contract_id
                            row.amount = row_data.amount;                // 🔹 from amount_invoiced
                            row.outstanding_amount = row_data.outstanding_amount
                            row.status = row_data.status;                // 🔹 from status
                            row.customer = row_data.customer,
                                row.bill_ship_code = row_data.bill_ship_code,
                                row.payment_id = row_data.payment_id
                        });
                        frm.refresh_field("payment_uploader");
                        frappe.msgprint(__("Payment data loaded successfully"));
                    } else {
                        frappe.msgprint(__("No due payments found"));
                    }
                }
            });
        }
    }
});
