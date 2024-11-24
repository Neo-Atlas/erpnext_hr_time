// Copyright (c) 2024, AtlasAero GmbH and contributors
// For license information, please see license.txt


frappe.ui.form.on('Worklog', {
    refresh: function (frm) {
        // Modify the employee field display dynamically to include full name.
        if (frm.doc.employee) {
            frappe.db.get_value('Employee', frm.doc.employee, 'employee_name', (r) => {
                if (r && r.employee_name) {
                    frm.fields_dict.employee.$wrapper.find('input').val(`${frm.doc.employee}: ${r.employee_name}`);
                }
            });
        }
    },
    validate: function(frm) {
        // Get the value of the log_time (datetime) field
        const enteredDatetime = frm.doc.log_time;
        
        // check if the entered log_time (datetime) is in the future
        if (enteredDatetime && new Date(enteredDatetime) > new Date()) {
            frappe.msgprint({
                title: __('WARNING'),
                message: __('The entered time cannot be in the future.'),
                indicator: 'red'
            });
            // Prevent Worklog form submission
            frappe.validated = false;
        }
    }
});
