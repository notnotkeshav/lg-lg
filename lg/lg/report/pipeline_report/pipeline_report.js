frappe.query_reports["Pipeline Report"] = {
    filters: [
        {
            fieldname: "customer",
            label: __("Customer Name"),
            fieldtype: "Link",
            options: "CRM Organization",
            reqd: 0
        },
        // {
        //     fieldname: "amc",
        //     label: __("AMC"),
        //     fieldtype: "Select",
        //     options: ["Yes", "No"],
        //     reqd: 0
        // },
        // {
        //     fieldname: "start_date",
        //     label: __("Start Date"),
        //     fieldtype: "Date",
        //     reqd: 0
        // },
        // {
        //     fieldname: "expiry_date",
        //     label: __("Expiry Date"),
        //     fieldtype: "Date",
        //     reqd: 0
        // },
        {
            fieldname: "payment_frequency",
            label: __("Payment Frequency"),
            fieldtype: "Select",
            options: ["","Monthly", "Quarterly", "Semi-Annually", "Annually"],
            reqd: 0
        }
    ]
};
