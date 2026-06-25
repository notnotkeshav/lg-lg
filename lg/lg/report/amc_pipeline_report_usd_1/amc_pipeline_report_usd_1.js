// // Copyright (c) 2025, extension and contributors
// // For license information, please see license.txt

// frappe.query_reports["AMC Pipeline Report USD 1"] = {
//     filters: [
//         {
//             fieldname: "customer",
//             label: "Customer",
//             fieldtype: "Link",
//             options: "CRM Organization"
//         },
//         {
//             fieldname: "project",
//             label: "Project",
//             fieldtype: "Link",
//             options:"Project"
//         },
//         {
//             fieldname: "region",
//             label: "Region",
//             fieldtype: "Select",
//             options: [],
//             on_change: function (query_report) {
//                 query_report.refresh();
//             }
//         },
//         {
//             fieldname: "branch",
//             label: "Branch",
//             fieldtype: "Select",
//             options: [],
//             on_change: function (query_report) {
//                 query_report.refresh();
//             }
//         },
//         {
//             fieldname: "vertical",
//             label: "Vertical",
//             fieldtype: "Link",
//             options: "CRM Industry"
//         },
//         {
//             fieldname: "deal_type",
//             label: "Contract Type",
//             fieldtype: "Select",
//             options: "\nWarranty Conversion\nAMC Renewal\nLost Warranty Conversion\nLost AMC Conversion"
//         },
//         {
//             fieldname: "year",
//             label: "Year(s)",
//             fieldtype: "MultiSelect",
//             default: "2025",
//             options: ["2024", "2025", "2026", "2027", "2028"],
//             get_data: function (txt) {
//                 return [
//                     { value: "2024", description: "2024" },
//                     { value: "2025", description: "2025" },
//                     { value: "2026", description: "2026" },
//                     { value: "2027", description: "2027" },
//                     { value: "2028", description: "2028" }
//                 ].filter(d => d.value.includes(txt));
//             }
//         },
// 		{
//         	"fieldname": "show_in_usd",
//             "label": "Show in USD",
//             "fieldtype": "Check",
//             "default": 1
//         },
//         {
//             "fieldname": "usd_rate",
//             "label": "USD Exchange Rate (optional)",
//             "fieldtype": "Float",
//             "depends_on": "eval:doc.show_in_usd",
//             "description": "Leave blank to fetch today's rate automatically"
//         }
//     ],

//     onload: function (report) {
//         // Fetch distinct Region and Branch from CRM Deal
//         frappe.call({
//             method: "frappe.client.get_list",
//             args: {
//                 doctype: "CRM Deal",
//                 fields: ["region", "branch"],
//                 limit_page_length: 1000
//             },
//             callback: function (r) {
//                 if (r.message) {
//                     const regions = [...new Set(r.message.map(d => d.region).filter(Boolean))];
//                     const branches = [...new Set(r.message.map(d => d.branch).filter(Boolean))];

//                     report.get_filter("region").df.options = ["", ...regions];
//                     report.get_filter("branch").df.options = ["", ...branches];

//                     report.get_filter("region").refresh();
//                     report.get_filter("branch").refresh();
//                 }
//             }
//         });

//         // Fetch today's USD exchange rate
//         frappe.call({
//             method: "/home/extension/frappe-bench/apps/lg/lg/lg/report/amc_pipeline_report_usd/amc_pipeline_report_usd.get_usd_exchange_rate", // <-- Replace with actual path
//             callback: function (r) {
//                 if (r.message) {
//                     report.get_filter("usd_rate").set_value(r.message);
//                 }
//             }
//         });
//     }
// };

// Copyright (c) 2025, extension and contributors
// For license information, please see license.txt

frappe.query_reports["AMC Pipeline Report USD 1"] = {
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
        },
        {
            fieldname: "show_in_usd",
            label: "Show in USD",
            fieldtype: "Check",
            default: 1
        }
    ],

    onload: function (report) {
        // Fetch distinct Region and Branch from CRM Deal
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
