import {EasyCheckinDialog} from "./easy_checkin_dialog";
import {EasyCheckinStatus} from "./easy_checkin_status";

document.bind_dashboard_easy_checkin = () => {
    EasyCheckinDialog.prepare_dashboard()
}

$(document).ready(function () {
    EasyCheckinDialog.singleton().preload()

    frappe.run_serially([
      () => EasyCheckinStatus.render(),
    ]);

    setInterval(function () {
        EasyCheckinStatus.render()
    }, 15_000)
});
