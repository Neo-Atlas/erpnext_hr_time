// Copyright (c) 2023, AtlasAero GmbH and contributors
// For license information, please see license.txt

frappe.ui.form.on('Flextime daily status', {
    validate: function (form) {
        if (form.doc.total_working_hours === "") {
            form.doc.total_working_hours = 0;
        }
    },
    refresh: function(frm) {
        let employee_id = frm.doc.employee;
        let date = frm.doc.date;

        // Call the custom API method to get the worklogs if employee_id and date exist
        if (employee_id && date) {
            frappe.call({
                method: "hr_time.api.worklog.api.get_worklogs_table_html",
                args: {
                    employee_id: employee_id,
                    date: date
                },
                callback: function(response) {
                    // Display the HTML response in a custom HTML field
                    frm.fields_dict["daily_worklogs_html"].$wrapper.html(response.message);
                }
            });
        }
    }
});


