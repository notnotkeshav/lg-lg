frappe.query_reports["AMC Pipeline Report"] = {
    filters: [
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
            options:"Project"
        },
        {
            fieldname: "region",
            label: "Region",
            fieldtype: "Select",
            options: [],
            on_change: function (query_report) {
                query_report.refresh();
            }
        },
        {
            fieldname: "branch",
            label: "Branch",
            fieldtype: "Select",
            options: [],
            on_change: function (query_report) {
                query_report.refresh();
            }
        },
        {
            fieldname: "vertical",
            label: "Vertical",
            fieldtype: "Link",
            options: "CRM Industry"
        },
        {
			fieldname: "deal_type",
			label: "Contract Type",
			fieldtype: "Select",
			options: "\nWarranty Conversion\nAMC Renewal\nLost Warranty Conversion\nLost AMC Conversion"
		},

        {
            fieldname: "year",
            label: "Year(s)",
            fieldtype: "MultiSelect",
            default: "2025",
            options: ["2024", "2025", "2026", "2027", "2028"],
            get_data: function (txt) {
                return [
                    { value: "2024", description: "2024" },
                    { value: "2025", description: "2025" },
                    { value: "2026", description: "2026" },
                    { value: "2027", description: "2027" },
                    { value: "2028", description: "2028" }
                ].filter(d => d.value.includes(txt));
            }
        }
    ],

    onload: function (report) {
        // Fetch distinct Region and Branch from CRM Deal and set options dynamically
        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "CRM Deal",
                fields: ["region", "branch"],
                limit_page_length: 1000
            },
            callback: function (r) {
                if (r.message) {
                    const regions = [...new Set(r.message.map(d => d.region).filter(Boolean))];
                    const branches = [...new Set(r.message.map(d => d.branch).filter(Boolean))];

                    report.get_filter("region").df.options = ["", ...regions];
                    report.get_filter("branch").df.options = ["", ...branches];

                    report.get_filter("region").refresh();
                    report.get_filter("branch").refresh();
                }
            }
        });
    }
};


