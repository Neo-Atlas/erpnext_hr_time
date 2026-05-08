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

window.CHECKIN_STATUS_REFRESH_INTERVAL_MS = 20_000;
window.WORK_DURATION_RECALC_INTERVAL_MS = 20_000;

// API Endpoints (add more API definitions here for global access)
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


document.bind_dashboard_easy_checkin = () => {
    EasyCheckinDialog.prepare_dashboard()
}

$(document).ready(function () {
    EasyCheckinDialog.singleton().preloadCheckinOptions()

    // Fetch buffer task ID once and cache it
    frappe.call({
        method: "hr_time.api.worklog.api.get_buffer_task",
        callback: function(r) {
            window.BUFFER_TASK_ID = r.message;
        }
    });

    frappe.run_serially([
      () => EasyCheckinStatus.render(),
    ]);

    setInterval(function () {
        EasyCheckinStatus.render()
    }, window.CHECKIN_STATUS_REFRESH_INTERVAL_MS)
});