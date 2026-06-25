frappe.query_reports["Opportunity HP Summary 2"] = {
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
            "options": "\nSales\nService",
            "default": "Sales"
        },
        {
            "fieldname": "date_range_type",
            "label": __("Date Range"),
            "fieldtype": "Select",
            "options": "Current Month\nPrevious Month\nPrevious 3 Months\nPrevious 6 Months\nCurrent Quarter\nPrevious Quarter\nCurrent Year\nPrevious Year\nCustom Range",
            "default": "Previous 6 Months"
        },
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.nowdate(), -6),
            "depends_on": "eval:doc.date_range_type && doc.date_range_type=='Custom Range'"

        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.nowdate(),
            "depends_on": "eval:doc.date_range_type && doc.date_range_type=='Custom Range'"
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
        {
            "fieldname": "chart_type",
            "label": __("Chart Type"),
            "fieldtype": "Select",
            "options": "bar\nline\npie\npercentage",
            "default": "bar"
        }
    ],

    formatter: function (value, row, column, data, default_formatter) {
        let v = default_formatter(value, row, column, data);
        if (column && column.fieldname === "group_html") return value;
        if (column && column.fieldname === "total_hp_display") {
            return `<div style='text-align:right;font-weight:600;'>${v}</div>`;
        }
        return v;
    },

    onload: function (report) {
        const oppCategory = report.get_filter('opportunity_category');
        if (oppCategory && !oppCategory.get_value()) {
            oppCategory.set_input('Sales');
        }

        const dateRangeFilter = report.get_filter("date_range_type");
        dateRangeFilter.df.on_change = () => {
            if (dateRangeFilter.get_value() !== "Custom Range") {
                report.refresh();
            }
        };

        // Clear filters button (same as before)
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
