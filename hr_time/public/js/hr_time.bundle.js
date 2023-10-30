import {EasyCheckinDialog} from "./easy_checkin_dialog";
import {EasyCheckinStatus} from "./easy_checkin_status";
import {NumberCardUtils} from "./utils";

document.hr_time = {
    utils: {
        number_card: NumberCardUtils
    }
}

document.bind_dashboard_easy_checkin = () => {
    EasyCheckinDialog.prepare_dashboard()
}

$(document).ready(function () {
    EasyCheckinDialog.singleton().preload()

    frappe.run_serially([
      () => EasyCheckinStatus.render(),
    ]);
});
