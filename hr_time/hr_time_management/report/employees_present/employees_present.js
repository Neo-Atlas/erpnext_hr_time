// Copyright (c) 2023, AtlasAero GmbH and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Employees present"] = {
	"filters": [
        {
            fieldname: 'status',
            label: __('Status'),
            fieldtype: 'Select',
            options: ["", "Work time", "Break"],
			default: "",
            default: frappe.defaults.get_user_default('company')
        },
	]
};
