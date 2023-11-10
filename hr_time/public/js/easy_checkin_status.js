import {EasyCheckinDialog} from "./easy_checkin_dialog";

export class EasyCheckinStatus {
    static render() {
        frappe.call({
            method: "hr_time.api.flextime.api.render_navbar_checkin_status",
            callback: (response) => {
                let statusElement = $('.navbar .checkin_status')
                statusElement.remove();

                $('.navbar .vertical-bar').after(response.message);
                statusElement.click(() => {
                    EasyCheckinDialog.singleton().show();
                });
            }
        });
    }
}