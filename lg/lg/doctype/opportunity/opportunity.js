// Copyright (c) 2024, extension and contributors
// For license information, please see license.txt


frappe.ui.form.on('Opportunity Item', {
    item_code: function(frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);

        if (row.item_code) {
            frappe.call({
                method: "lg.lg.doctype.opportunity.opportunity.get_warranty",
                args: {
                    item_code: row.item_code
                },
                callback: function(r) {
                    if (r.message && r.message.length > 0) {
                        let warranty = r.message[0]; 

                        if (warranty.two_months_before) {
                            
                            frm.set_value("custom_creation_date", warranty.two_months_before);
                            frm.set_df_property("custom_creation_date", "read_only", 1);
                            frappe.msgprint(__('Custom Creation Date set to two months before Warranty expiry date.'));
                        }
                    } else {
                        frappe.msgprint(__('No Warranty found for the selected Item Code: {0}', [row.item_code]));
                    }
                }
            });
        }
    }
});
