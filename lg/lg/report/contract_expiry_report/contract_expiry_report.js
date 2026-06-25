// 
frappe.query_reports["Contract Expiry Report"] = {
    filters: [
        {
            fieldname: "period_type",
            label: "Select Period Type",
            fieldtype: "Select",
            options: ["Days", "Months"],
            default: "Days",
            reqd: 1,
            on_change: function (report) {
                const periodType = frappe.query_report.get_filter_value('period_type');

                // Show/hide relevant filters
                let days_filter = frappe.query_report.get_filter('days_value');
                let months_filter = frappe.query_report.get_filter('months_value');

                if (periodType === "Days") {
                    days_filter.toggle(true);
                    months_filter.toggle(false);
                    frappe.query_report.set_filter_value('months_value', null);
                } else {
                    days_filter.toggle(false);
                    months_filter.toggle(true);
                    frappe.query_report.set_filter_value('days_value', null);
                }
            }
        },
        {
            fieldname: "days_value",
            label: "Number of Days",
            fieldtype: "Int",
            default: 30
        },
        {
            fieldname: "months_value",
            label: "Number of Months",
            fieldtype: "Int",
            default: 1
        }
    ],

    onload: function (report) {
        const periodType = frappe.query_report.get_filter_value('period_type') || "Days";

        let days_filter = frappe.query_report.get_filter('days_value');
        let months_filter = frappe.query_report.get_filter('months_value');

        if (periodType === "Days") {
            days_filter.toggle(true);
            months_filter.toggle(false);
        } else {
            days_filter.toggle(false);
            months_filter.toggle(true);
        }
    }
};
