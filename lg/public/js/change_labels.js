frappe.ready(function () {

    function update_dashboard_titles() {
        console.log("executing the dynamaic labels")

        let today = frappe.datetime.nowdate();
        let todayFormatted = frappe.datetime.str_to_user(today);

        let now = new Date();
        let monthName = now.toLocaleString('default', { month: 'long' });
        let year = now.getFullYear();

        // Loop through all number cards
        $('.number-card-widget').each(function () {

            let title = $(this).find('.widget-title').text();

            // TODAY Cards
            if (title.includes("Created - Today")) {
                let newTitle = title.replace("Today", todayFormatted);
                $(this).find('.widget-title').text(newTitle);
            }

            // THIS MONTH Cards
            if (title.includes("Created - This Month")) {
                let newTitle = title.replace("This Month", monthName + " " + year);
                $(this).find('.widget-title').text(newTitle);
            }

            if (title.includes("Expiring - This Month")) {
                let newTitle = title.replace("This Month", monthName + " " + year);
                $(this).find('.widget-title').text(newTitle);
            }

        });
    }

    setTimeout(update_dashboard_titles, 1000);
});