import {EasyCheckinDialog} from "./easy_checkin_dialog";

export class EasyCheckinStatus {
    static render() {
        frappe.call({
            method: "hr_time.api.flextime.api.render_navbar_checkin_status",
            callback: (response) => {
                $('.navbar .checkin_status').remove();
                $('.navbar .vertical-bar').after(response.message);
                $('.navbar .checkin_status').click(() => {
                    EasyCheckinDialog.singleton().show();
                });
            }
        });
    }
}