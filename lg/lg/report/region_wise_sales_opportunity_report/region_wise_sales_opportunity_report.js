// Copyright (c) 2025, extension and contributors
// For license information, please see license.txt

frappe.query_reports["Region-wise Sales Opportunity Report"] = {
	"filters": [
{
            fieldname: "year",
            label: __("Year"),
            fieldtype: "Int",
            default: new Date().getFullYear()
        },
        {
            fieldname: "region",
            label: __("Region"),
            fieldtype: "Link",
            options: "Region Master"
        },
        {
            fieldname: "branch",
            label: __("Branch"),
            fieldtype: "Link",
            options: "Region Branches"
        }
    ],

    formatter: function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        // List of month fieldnames from backend (Jan, Feb, ...)
        const months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

        if (months.includes(column.fieldname) && data && parseInt(value) > 0) {
            let monthNumber = months.indexOf(column.fieldname) + 1; // 1-12
            let year = frappe.query_report.get_filter_value("year");

            // Build route params
            let filters = {
                region: data.region,
                branch: data.branch,
                deal_category: "Sales",
                warranty_expiry_date: [
                    "between",
                    [
                        `${year}-${monthNumber.toString().padStart(2, "0")}-01`,
                        `${year}-${monthNumber.toString().padStart(2, "0")}-31`
                    ]
                ]
            };

            // Create clickable span with onclick
            return `<span style="color:blue;cursor:pointer;font-weight:bold"
                        onclick='frappe.set_route("List", "CRM Deal", ${JSON.stringify(filters)})'>
                        ${value}
                    </span>`;
        }

        return value;
    }
};