// Copyright (c) 2024, AtlasAero GmbH and contributors
// For license information, please see license.txt


frappe.ui.form.on('Worklog', {
    validate: function(frm) {
        // Get the value of the log_time (datetime) field
        const enteredDatetime = frm.doc.log_time;
        
        // check if the entered log_time (datetime) is in the future
        if (enteredDatetime && new Date(enteredDatetime) > new Date()) {
            frappe.msgprint({
                title: __('WARNING'),
                message: __('The entered time cannot be in the future.'),
                indicator: 'red'  // The indicator color
            });
            // Prevent Worklog form submission
            frappe.validated = false;
        }
    }
});
