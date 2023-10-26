export class EasyCheckinDialog {
    options = [];
    default = "";

    preload() {
        frappe.call({
            method: "hr_time.api.flextime.api.get_easy_checkin_options",
            callback: (response) => {
                this.options = response.message.options;
                this.default = response.message.default;
            }
        });
    }

    show() {
        let dialog = new frappe.ui.Dialog({
            title: __("Checkin"),
            fields: [
                {
                    label: 'Action',
                    fieldname: 'action',
                    fieldtype: 'Select',
                    options: this.options,
                    default: this.default
                }
            ],
            size: 'small', // small, large, extra-large
            primary_action_label: __("Submit"),
            primary_action(values) {
                console.log(values);
                dialog.hide();
            }
        });

        dialog.show()
    }

    static prepare() {
        let dialog = new EasyCheckinDialog();
        dialog.preload();

        document
            .getElementById("hr_time_number_card_checkin_status")
            .querySelector(".checkin_status")
            .onclick = function () {
            dialog.show();
        }
    }
}


