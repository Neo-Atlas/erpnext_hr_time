// Copyright (c) 2023, AtlasAero GmbH and contributors
// For license information, please see license.txt

frappe.ui.form.on('Trigger HR time management batch jobs', {
    process_daily_flextime_status: (frm) => {
        frappe.call({
            method: "hr_time.api.flextime.api.generate_daily_flextime_status",
            freeze: true,
            callback: result => {
                console.log(result)
            }
        });
    }
});
