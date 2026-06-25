// Copyright (c) 2025, extension and contributors
// For license information, please see license.txt

frappe.query_reports["Opportunity HP-Tonnes Summery"] = {
	 "filters": [
        {
            "fieldname": "group_by",
            "label": __("Group By"),
            "fieldtype": "Select",
            "options": "Project\nBranch\nAM\nRegion\nRSM",
            "default": "Project"
        },
        {
            "fieldname": "opportunity_category",
            "label": __("Opportunity Category"),
            "fieldtype": "Select",
            "options": "\nSales\nService",   // blank first option allowed
            "default": "Sales"
        },
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.nowdate(), -6) // default last 6 months
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.nowdate()
        },
        {
            "fieldname": "project",
            "label": __("Project (IL)"),
            "fieldtype": "Link",
            "options": "Project"
        },
        {
            "fieldname": "branch",
            "label": __("Branch"),
            "fieldtype": "Link",
            "options": "Region Branches"
        },
        {
            "fieldname": "region",
            "label": __("Region"),
            "fieldtype": "Link",
            "options": "Region Master"
        },
        // {
        //     "fieldname": "am",
        //     "label": __("AM (Account Manager)"),
        //     "fieldtype": "Data",
        //     "description": __("Matches Branch Head, Opportunity Account Manager or Owner")
        // },
        {
            "fieldname": "chart_type",
            "label": __("Chart Type"),
            "fieldtype": "Select",
            "options": "bar\nline\npie\npercentage",
            "default": "bar"
        },
        {
            "fieldname": "bar_chart_wise",
            "label": __("Chart Basis Of"),
            "fieldtype": "Select",
            "options": "HP\nTonne",
            "default": "HP"
        }
    ],

    // custom formatter to style the HP cell & keep HTML column rendering
    "formatter": function (value, row, column, data, default_formatter) {
        // default formatting first (handles number and links)
        let v = default_formatter(value, row, column, data);

        // our server returns group_html already as HTML in the first column,
        // so we simply return it (avoid escaping)
        if (column && column.fieldname === "group_html") {
            return value;
        }

        // highlight Total HP column
        if (column && column?.fieldname?.includes("total_in_warrenty_hp", "total_out_warrenty_hp", "total_amc_active_hp", "total_amc_expired_hp", "total_in_warrenty_tonne", "total_out_warrenty_tonne", "total_amc_active_tonne", "total_amc_expired_tonne")) {
            // make bold and right-aligned
            return "<div style='text-align:right;font-weight:600;'>" + v + "</div>";
        }

        return v;
    },

    // when filters change, automatically refresh chart type default and set nice date presets
    "onload": function(report) {
        // ensure Opportunity Category default is Sales (in case users remove)
        const f = report.get_filter('opportunity_category');
        if (f && !f.get_value()) {
            f.set_input('Sales');
        }

        // Add a quick "Top 10" menu to the report page
        // report.page.add_inner_button(__('Top 10'), function() {
        //     // set a limit by changing filters and refreshing - we didn't implement limit on server,
        //     // but users often request top 10; here, we'll simply refresh and visually suggest top rows.
        //     frappe.msgprint(__('Use the "Top N" server-side filter if you need strict limits.'));
        // });
    }
};
