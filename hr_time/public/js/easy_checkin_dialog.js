import {EasyCheckinStatus} from "./easy_checkin_status";

export class EasyCheckinDialog {
    options = [];
    default = "";

    refresh_buttons;

    /**
     * Preloads the current checkin status
     */
    preload() {
        frappe.call({
            method: "hr_time.api.flextime.api.get_easy_checkin_options",
            callback: (response) => {
                this.options = response.message.options;
                this.default = response.message.default;
            }
        });
    }

    /**
     * Checks if the employee has worklogs today before showing the dialog
     */
    show() {
        let checkin_dialog = this;

        // First, fetch the employee_id from the backend
        frappe.call({
            method: "hr_time.api.employee.api.get_current_employee_id",  // Server-side call to fetch employee_id
            callback: function(response) {
                const employee_id = response.message;  // The employee_id returned from the server

                if (!employee_id) {
                    frappe.throw(__('No employee ID found for the current user.'));
                    return;
                }

                // Create the dialog only after the employee_id is fetched
                let dialog = new frappe.ui.Dialog({
                    title: __("Checkin"),
                    fields: [
                        {
                            label: 'Action',
                            fieldname: 'action',
                            fieldtype: 'Select',
                            options: checkin_dialog.options,
                            default: checkin_dialog.default
                        },
                        {
                            fieldtype: 'Button',
                            label: 'Add Worklog',
                            fieldname: 'add_log',
                            click() {
                                // Open a new Worklog form
                                frappe.new_doc('Worklog');
                            }
                        }
                    ],
                    size: 'small',  // small, large, extra-large
                    primary_action_label: __("Submit", undefined, "checkin"),
                    primary_action(values) {
                        frappe.call({
                            method: "hr_time.api.flextime.api.submit_easy_checkin",
                            args: {
                                action: values.action,
                                employee_id: employee_id  // Pass the employee_id to the backend
                            },
                            callback: (response) => {
                                checkin_dialog.refresh_dashboard();
                                EasyCheckinStatus.render();
                                checkin_dialog.preload();

                                let message = "Successfully checked in";

                                switch (values.action) {
                                    case "Break":
                                        message = "Successfully checked out for break";
                                        break;
                                    case "End of work":
                                        message = "Successfully checked out for end of work";
                                        break;
                                }

                                frappe.show_alert({
                                    message: __(message),
                                    indicator: 'green'
                                }, 5);
                            }
                        });

                        dialog.hide();
                    }
                });

                dialog.show();

                // Check if the employee has worklogs today
                frappe.call({
                    method: "hr_time.api.worklog.api.has_employee_made_worklogs_today",  // Server-side method to check worklogs
                    args: { employee_id: employee_id },
                    callback: function(response) {
                        let hasWorklogs = response.message;
                        
                        // Apply conditional styling to the "Add Worklog" button based on worklogs status
                        if (hasWorklogs) {
                            dialog.$wrapper.find('button[data-fieldname="add_log"]').css({
                                'background-color': 'var(--bg-green)',
                                'color': '#000',
                                'border': 'none',
                                'margin-left': 'auto',
                                'float': 'right'
                            });
                        } else {
                            dialog.$wrapper.find('button[data-fieldname="add_log"]').css({
                                'background-color': 'maroon',
                                'color': '#fff',
                                'border': 'none',
                                'margin-left': 'auto',
                                'float': 'right'
                            });
                        }
                    }
                });
            }
        });
    }

    refresh_dashboard() {
        if (this.refresh_buttons === undefined) {
            return;
        }

        for (let button of this.refresh_buttons) {
            button.click()
        }
    }

    /**
     * Binds events for numer card of dashboard
     */
    static prepare_dashboard() {
        let dialog = EasyCheckinDialog.singleton()

        document
            .getElementById("hr_time_number_card_checkin_status")
            .querySelector(".checkin_status")
            .onclick = function () {
            dialog.show();
        }

        dialog.refresh_buttons = [
            document
                .querySelector('[number_card_name="Checkin status"]')
                .querySelector('[data-action="action-refresh"]'),
            document
                .querySelector('[number_card_name="Employees present"]')
                .querySelector('[data-action="action-refresh"]'),
            document
                .querySelector('[quick_list_name="Employee Checkin"]')
                .querySelector('.refresh-list.btn')
        ]

        setTimeout(() => {
            dialog.refresh_dashboard();
        }, 15_000);
    }

    /**
     * Returns/Creates the singleton instance
     */
    static singleton() {
        if (window.easy_checkin_dialog === undefined) {
            window.easy_checkin_dialog = new EasyCheckinDialog();
        }

        return window.easy_checkin_dialog;
    }
}


