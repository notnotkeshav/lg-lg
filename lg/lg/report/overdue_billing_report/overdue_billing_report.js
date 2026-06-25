frappe.query_reports["Overdue Billing Report"] = {
    "filters": [
        {
            fieldname: "to_date",
            label: "To Date",
            fieldtype: "Date",
            reqd: 1,
            default: frappe.datetime.get_today()
        },
        {
            fieldname: "customer",
            label: "Customer",
            fieldtype: "Link",
            options: "CRM Organization"
        },
        {
            fieldname: "project",
            label: "Project",
            fieldtype: "Link",
			options:"Project",
			default:""
        }
    ]
};
