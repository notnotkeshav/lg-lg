frappe.ui.form.on("Project", {
    refresh: function (frm) {
        if (!frm.doc.__islocal && frm.doc.expiry_date) {

            let today = frappe.datetime.nowdate();

            // Show button only if expiry date passed
            if (frm.doc.expiry_date < today) {
                frm.add_custom_button(__('Create AMC Opportunity'), function () {
                    frappe.model.open_mapped_doc({
                        method: "lg.lg.doctype.project.project.make_crm_deal",
                        frm: frm
                    });
                });
            }
        }
    },
    onload: function (frm) {
        if (frm.doc.is_new() && !frm.doc.project_name) {
            frm.set_value("project_name", "IL")
        }
    },
    project_name(frm) {
        if (frm.doc.project_name && !frm.doc.project_name.startsWith("IL")) {
            frm.set_value("project_name", "")

            frappe.throw("Project Name must start with 'IL'");
        }
    }

});

