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
window.MESSAGES = MESSAGES || []

// Defined constants/configs for the module (eg. for local storage keys)
window.HR_TIME = window.HR_TIME || {};

HR_TIME.LS_KEYS = {
    PREV_WFH_PREF: 'neo_hr_time_last_wfh_value'
};

const CHECKIN_STATUS_REFRESH_INTERVAL_MS = 15_000;

document.bind_dashboard_easy_checkin = () => {
    EasyCheckinDialog.prepare_dashboard()
}

$(document).ready(function () {
    EasyCheckinDialog.singleton().preloadCheckinOptions()

    frappe.run_serially([
      () => EasyCheckinStatus.render(),
    ]);

    setInterval(function () {
        EasyCheckinStatus.render()
    }, CHECKIN_STATUS_REFRESH_INTERVAL_MS)
});