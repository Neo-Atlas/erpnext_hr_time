// Copyright (c) 2023, AtlasAero GmbH and contributors
// For license information, please see license.txt

frappe.ui.form.on('Flextime definition', {
	validate: function (form) {
        form.doc.monday_working_hours = fix_empty_working_hours(form.doc.monday_working_hours);
        form.doc.tuesday_working_hours = fix_empty_working_hours(form.doc.tuesday_working_hours);
        form.doc.wednesday_working_hours = fix_empty_working_hours(form.doc.wednesday_working_hours);
        form.doc.thursday_working_hours = fix_empty_working_hours(form.doc.thursday_working_hours);
        form.doc.friday_working_hours = fix_empty_working_hours(form.doc.friday_working_hours);
        form.doc.saturday_working_hours = fix_empty_working_hours(form.doc.saturday_working_hours);
        form.doc.sunday_working_hours = fix_empty_working_hours(form.doc.sunday_working_hours);

        validate_core_time(form.doc.monday_core_time_start, form.doc.monday_core_time_end, "Monday");
        validate_core_time(form.doc.tuesday_core_time_start, form.doc.tuesday_core_time_end, "Tuesday");
        validate_core_time(form.doc.wednesday_core_time_start, form.doc.wednesday_core_time_end, "Wednesday");
        validate_core_time(form.doc.thursday_core_time_start, form.doc.thursday_core_time_end, "Thursday");
        validate_core_time(form.doc.friday_core_time_start, form.doc.friday_core_time_end, "Friday");
        validate_core_time(form.doc.saturday_core_time_start, form.doc.saturday_core_time_end, "Saturday");
        validate_core_time(form.doc.sunday_core_time_start, form.doc.sunday_core_time_end, "Sunday");
    }
});

/**
 * Validates start and end time of core time
 */
function validate_core_time(start, end, day_string) {
    if (start <= end) {
        return;
    }

    if (start === undefined && end === undefined) {
        return;
    }

    if (end === undefined) {
        frappe.msgprint(__("{0}: The end of core working time cannot be empty if a start is set.", [__(day_string)]));
        frappe.validated = false;
        return;
    }

    if (start === undefined) {
        frappe.msgprint(__("{0}: The start of core working time cannot be empty if a end is set.", [__(day_string)]));
        frappe.validated = false;
        return;
    }

    frappe.msgprint(__("{0}: The end of the core working time must be after the start.", [__(day_string)]));
    frappe.validated = false;
}

/**
 * Sets working hours to 0 if empty
 */
function fix_empty_working_hours(field) {
    if (field === "") {
        return 0;
    }

    return field;
}