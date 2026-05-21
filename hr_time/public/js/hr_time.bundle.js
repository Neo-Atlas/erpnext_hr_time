import MESSAGES from "./constants/messages.js";
import { FrappeUtils } from "./utils/frappe_utils.js";
import { JsUtils } from "./utils/common_utils.js";
import { FlextimeApi } from "./api/flextime.api.js";
import { EasyCheckinDialog } from "./easy_checkin_dialog.js";
import { EasyCheckinStatus } from "./easy_checkin_status.js";

// Attach to global namespace
window.FlextimeApi = FlextimeApi;
window.FrappeUtils = FrappeUtils;
window.JsUtils = JsUtils;
window.MESSAGES = MESSAGES || [];

// Defined constants/configs for the module (eg. for local storage keys)
window.HR_TIME = window.HR_TIME || {};

window.refreshCheckinOptions = function() {
    const dialog = EasyCheckinDialog.singleton();
    if (dialog) {
        dialog.preloadCheckinOptions();
    }
};

HR_TIME.LS_KEYS = {
    PREV_WFH_PREF: 'neo_hr_time_last_wfh_value'
};

window.WORK_DURATION_RECALC_INTERVAL_MS = 20_000;

// API Endpoints (add more API definitions here for global access/use in multiple files)
window.API = {
    FLEXTIME: {
        GET_OPTIONS: "hr_time.api.flextime.api.get_easy_checkin_options",
        SUBMIT_CHECKIN: "hr_time.api.flextime.api.submit_easy_checkin",
    },
    WORKLOG: {
        GET_CONTEXT: "hr_time.api.worklog.api.get_worklog_context",
        PREPARE_CHECKOUT: "hr_time.api.worklog.api.prepare_worklog_for_checkout",
        SAVE_AND_CHECKOUT: "hr_time.api.worklog.api.save_and_checkout",
    },
    EMPLOYEE: {
        GET_CURRENT_EMPLOYEE_ID: "hr_time.api.employee.api.get_current_employee_id",
        GET_CURRENT_EMPLOYEE: "hr_time.api.employee.api.get_current_employee"
    },
    CLIENT: {
        GET_DOC: "frappe.client.get",
    },
};

$(document).ready(function () {
    // Set employee ID on EasyCheckinStatus as soon as possible
    FlextimeApi.fetchCurrentEmployeeId()
        .then(empId => {
            EasyCheckinStatus.setCurrentEmployeeId(empId);
            if (!empId) {
                console.warn("No employee record found (admin user) - check-in features disabled");
                // Hide checkin-status elevemt from UI for admins
                $('.navbar .checkin_status').hide();
            }
        }).catch(error => {
            console.error("Failed to set employee ID:", error);
            EasyCheckinStatus.setCurrentEmployeeId(null);
        });

    EasyCheckinDialog.singleton().preloadCheckinOptions()

    // Fetch buffer task ID once and cache it
    frappe.call({
        method: "hr_time.api.worklog.api.get_buffer_task",
        callback: function(r) {
            window.BUFFER_TASK_ID = r.message;
        }
    });

    // Initialize realtime subscription for checkin status updates and related UI refreshes and bindings
    EasyCheckinStatus.init();
    
    // Initial navbar render using API endpoint and setup click handler to open checkin dialog
    frappe.run_serially([
        () => frappe.call({
            method: "hr_time.api.flextime.api.render_navbar_checkin_status",
            callback: (response) => {
                $('.navbar .checkin_status').remove();
                $('.navbar .vertical-bar').after(response.message);
                $('.navbar .checkin_status').click(() => {
                    EasyCheckinDialog.singleton().show();
                });
            }
        })
    ]);
});