// Copyright (c) 2025, extension and contributors
// For license information, please see license.txt

frappe.query_reports["Opportunity HP Summary 3"] = {
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
			"fieldname": "date_range_type",
			"label": __("Date Range"),
			"fieldtype": "Select",
			"options": "Current Month\nPrevious Month\nPrevious 3 Months\nPrevious 6 Months\nCurrent Quarter\nPrevious Quarter\nCurrent Year\nPrevious Year\nCustom Range",
			"default": "Custom Range",
			"on_change": function(query_report) {
				let filter = frappe.query_report.get_filter('date_range_type');
				let value = filter.get_value();

				let today = frappe.datetime.nowdate();
				let from_date = today;
				let to_date = today;

				if (value === "Current Month") {
					from_date = frappe.datetime.month_start(today);
					to_date = frappe.datetime.month_end(today);
				} 
				else if (value === "Previous Month") {
					let prev = frappe.datetime.add_months(today, -1);
					from_date = frappe.datetime.month_start(prev);
					to_date = frappe.datetime.month_end(prev);
				} 
				else if (value === "Previous 3 Months") {
					from_date = frappe.datetime.add_months(today, -3);
					to_date = today;
				} 
				else if (value === "Previous 6 Months") {
					from_date = frappe.datetime.add_months(today, -6);
					to_date = today;
				} 
				else if (value === "Current Quarter") {
					from_date = frappe.datetime.quarter_start(today);
					to_date = frappe.datetime.quarter_end(today);
				} 
				else if (value === "Previous Quarter") {
					let prev_q = frappe.datetime.add_months(today, -3);
					from_date = frappe.datetime.quarter_start(prev_q);
					to_date = frappe.datetime.quarter_end(prev_q);
				} 
				else if (value === "Current Year") {
					from_date = frappe.datetime.year_start(today);
					to_date = frappe.datetime.year_end(today);
				} 
				else if (value === "Previous Year") {
					let prev_year = frappe.datetime.add_years(today, -1);
					from_date = frappe.datetime.year_start(prev_year);
					to_date = frappe.datetime.year_end(prev_year);
				} 
				else {
					return; // Custom Range
				}

				frappe.query_report.set_filter_value({
					"from_date": from_date,
					"to_date": to_date
				});

				frappe.query_report.refresh(); // ✅ Auto refresh
			}
		},
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.nowdate(), -6),
			"read_only_depends_on": "eval:doc.date_range_type!='Custom Range'"
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.nowdate(),
			"read_only_depends_on": "eval:doc.date_range_type!='Custom Range'"
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
        if (column && column.fieldname === "total_hp_display") {
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
        const btn = report.page.add_inner_button(__("Clear Filters"), () => {
            report.filters.forEach(f => {
                if (f.df.default) f.set_input(f.df.default);
                else f.set_input("");
            });
            report.refresh();
        });

        btn.removeClass("btn-default").addClass("btn-primary").css({
            "background-color": "#fa87adff",
            "color": "#fff",
            "border": "none",
            "border-radius": "6px",
            "padding": "6px 12px",
            "font-weight": "500"
        }).hover(
            function () { $(this).css("background-color", "#ff1c7bff"); },
            function () { $(this).css("background-color", "#fa87adff"); }
        );
    
	}

};
