
frappe.query_reports["CRM Contract Summary Report"] = {
    filters: [
        {
            fieldname: "customer_name",
            label: __("Customer"),
            fieldtype: "Link",
            options: "Customer"
        },
        {
            fieldname: "branch",
            label: __("Branch"),
            fieldtype: "Link",
            options: "Branch"
        },
        {
            fieldname: "region",
            label: __("Zone"),
            fieldtype: "Data"
        },
        {
            fieldname: "ssd_name_dealer",
            label: __("Dealer Name"),
            fieldtype: "Data"
        },
        {
            fieldname: "bill_ship_code",
            label: __("Bill To Code"),
            fieldtype: "Data"
        },
        {
            fieldname: "from_start_date",
            label: __("From Start Date"),
            fieldtype: "Date"
        },
        {
            fieldname: "to_start_date",
            label: __("To Start Date"),
            fieldtype: "Date"
        },
        {
            fieldname: "from_expiry_date",
            label: __("From Expiry Date"),
            fieldtype: "Date"
        },
        {
            fieldname: "to_expiry_date",
            label: __("To Expiry Date"),
            fieldtype: "Date"
        }
    ]
};
