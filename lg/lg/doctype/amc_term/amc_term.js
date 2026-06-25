frappe.ui.form.on("AMC Term", {
	start_date_as_per_po: function (frm) {
        generate_billing_schedule(frm)
    },
    end_date_as_per_po: function (frm) {
        generate_billing_schedule(frm)
    },
    billing_terms: function (frm) {
        generate_billing_schedule(frm)
    },
    payment_term: function (frm) {
        generate_billing_schedule(frm)
    },
    payment_frequency: function (frm) {
        generate_billing_schedule(frm)
    },
    refresh:function(frm){
        frm.add_custom_button(__('Create Sub Contract'), function () {
            frappe.model.open_mapped_doc({
                method: "lg.lg.doctype.amc_term.amc_term.make_crm_contract",
                frm: frm
            });
        });
        
    }
});

async function generate_billing_schedule(frm) {
    const {
        start_date,
        end_date,
        payment_frequency,
        payment_term,
        amount: total_amount,
    } = frm.doc;

    const billing_terms = frm.doc.billing_terms || "Post"; // Pre or Post or Advance

    if (!start_date || !end_date || !payment_frequency || !total_amount) {
        return;
    }

    frm.clear_table("billing_schedule");

    // =====================================================
    // 🔹 Special Case: 100% (Partial Contract)
    // =====================================================
    if (payment_frequency === "100% for Partial Contract") {

        let billing_date = (billing_terms === "Advance")
            ? frappe.datetime.str_to_obj(start_date)
            : frappe.datetime.str_to_obj(end_date);

        // 🔹 Get minimum days row from Payment Term
        let min_row = null;
        if (payment_term) {
            await frappe.db.get_doc("Pay Term", payment_term).then(doc => {
                if (doc && doc.payment_term_portions?.length > 0) {
                    min_row = doc.payment_term_portions.reduce((prev, curr) => {
                        return (curr.days || 0) < (prev.days || 0) ? curr : prev;
                    });
                }
            });
        }

        let min_days = min_row ? min_row.days : 0;

        const row = frm.add_child("billing_schedule");
        row.billing_date = frappe.datetime.obj_to_str(billing_date);

        let payment_date_obj = new Date(billing_date.getTime());
        payment_date_obj.setDate(payment_date_obj.getDate() + min_days);
        row.payment_date = frappe.datetime.obj_to_str(payment_date_obj);

        row.amount = flt(total_amount);
        row.billing_term = "Full Payment";
        row.status = "Pending";
        row.invoice_portion = 100;

        frm.refresh_field("billing_schedule");
        return;
    }

    // =====================================================
    // 🔹 Normal Frequency Logic
    // =====================================================

    const freq_map = {
        "Monthly": 1,
        "Quarterly": 3,
        "Semi-Annually": 6,
        "Annually": 12
    };

    const months_to_add = freq_map[payment_frequency];
    if (!months_to_add) return;

    let term_counter = 1;
    let end_obj = frappe.datetime.str_to_obj(end_date);
    let dates = [];

    // 🔹 If billing_terms is Advance, start with start_date
    if (billing_terms === "Advance") {
        dates.push(frappe.datetime.str_to_obj(start_date));
    }

    let current = frappe.datetime.str_to_obj(start_date);

    while (true) {
        let next = new Date(current.getTime());
        next.setMonth(next.getMonth() + months_to_add);

        if (next >= end_obj) {
            dates.push(end_obj);
            break;
        } else {
            dates.push(next);
            current = next;
        }
    }

    // 🔹 Remove duplicate end date in Advance case
    if (billing_terms === "Advance" && dates.length > 1) {
        dates.pop();
    }

    const per_row_amount = dates.length > 0 ? flt(total_amount) / dates.length : 0;

    // 🔹 Get minimum days row from Payment Term
    let min_row = null;
    if (payment_term) {
        await frappe.db.get_doc("Pay Term", payment_term).then(doc => {
            if (doc && doc.payment_term_portions?.length > 0) {
                min_row = doc.payment_term_portions.reduce((prev, curr) => {
                    return (curr.days || 0) < (prev.days || 0) ? curr : prev;
                });
            }
        });
    }

    let min_days = min_row ? min_row.days : 0;
    let min_invoice_portion = min_row ? min_row.invoice_portion : 100;

    for (let i = 0; i < dates.length; i++) {
        const row = frm.add_child("billing_schedule");
        row.billing_date = frappe.datetime.obj_to_str(dates[i]);

        let billing_date_obj = new Date(dates[i].getTime());
        billing_date_obj.setDate(billing_date_obj.getDate() + min_days);
        row.payment_date = frappe.datetime.obj_to_str(billing_date_obj);

        row.amount = per_row_amount;
        row.billing_term = get_ordinal(term_counter++) + " Term";
        row.status = "Pending";
        row.invoice_portion = min_invoice_portion;
    }

    frm.refresh_field("billing_schedule");
}

function get_ordinal(n) {
    const s = ["th", "st", "nd", "rd"], v = n % 100;
    return n + (s[(v - 20) % 10] || s[v] || s[0]);
}