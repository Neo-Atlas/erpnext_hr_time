import {EasyCheckinDialog} from "./easy_checkin_dialog";
import {EasyCheckinStatus} from "./easy_checkin_status";


// Defined constants/configs for the module (eg. for local storage keys)
window.HR_TIME = window.HR_TIME || {};

HR_TIME.LS_KEYS = {
    PREV_WFH_PREF: 'neo_hr_time_last_wfh_value'
};

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
    }, 15_000)
});