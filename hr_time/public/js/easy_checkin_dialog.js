import { EasyCheckinStatus } from "./easy_checkin_status";

/**
 * Class representing the EasyCheckinDialog for managing employee check-ins.
 */
export class EasyCheckinDialog {
  /**
   * Array of options available for check-in actions.
   * @type {Array<string>}
   */
  options = [];

  /**
   * Default check-in action.
   * @type {string}
   */
  default = "";

  /**
   * Indicatesif the employee has worklogs for today.
   * @type {boolean}
   */
  hasWorklogs = false;

  /**
   * Reference to the Frappe dialog UI instance.
   * @type {Object}
   */
  dialogUI;

  /**
   * Array of buttons to refresh the dashboard UI.
   * @type {Array<Element>}
   */
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
      },
    });
  }

  /**
   * Displays the check-in dialog if the employee has worklogs for today.
   * Checks if the current employee has worklogs before showing the dialog.
   */
  show() {
    frappe.call({
      method: "hr_time.api.employee.api.get_current_employee_id",
      callback: (response) => {
        const employee_id = response.message;

        if (!employee_id) {
          frappe.throw(__("No employee ID found for the current user"));
          return;
        }

        this.checkIfEmployeeHasWorklogs(employee_id);
      },
    });
  }

  /**
   * Checks if the employee has worklogs for today using the provided employee ID.
   * @param {string} employee_id - The ID of the employee to check for worklogs.
   */
  checkIfEmployeeHasWorklogs(employee_id) {
    frappe.call({
      method: "hr_time.api.worklog.api.has_employee_made_worklogs_today",
      args: { employee_id: employee_id },
      callback: (response) => {
        this.hasWorklogs = response.message;
        this.createCheckinDialog(employee_id);
      },
    });
  }

  /**
   * Creates and displays the check-in dialog with options and actions.
   * @param {string} employee_id - The ID of the employee.
   */
  createCheckinDialog(employee_id) {
    this.dialogUI = new frappe.ui.Dialog({
      title: `&#9745;&nbsp;${__("Checkin")}`, //checkbox-icon; space; label
      fields: this.getDialogFields(employee_id),
      size: "small",
      primary_action_label: __("Submit", undefined, "checkin"),
      primary_action: (values) => this.submitCheckin(values, employee_id),
    });

    this.dialogUI.show();
    this.initializeDialog();
  }

  /**
   * Returns the configuration of fields to be displayed in the check-in dialog.
   * @param {string} employee_id - The ID of the employee.
   * @returns {Array<Object>} - The fields configuration for Frappe's UI dialog.
   */
  getDialogFields(employee_id) {
    return [
      {
        label: "Action",
        fieldname: "action",
        fieldtype: "Select",
        options: this.options,
        default: this.default,
        change: () => this.updateDialogBasedOnAction(),
      },
      {
        fieldtype: "Section Break",
        depends_on: 'eval: doc.action === "End of work"',
      },
      {
        fieldname: "worklog_section",
        fieldtype: "HTML",
        options: this.getWorklogSectionHTML(),
      },
      {
        fieldname: "worklog_box",
        fieldtype: "Text",
        placeholder: __("Describe your task here") + "...",
      },
      {
        fieldtype: "Button",
        label: "✔",
        fieldname: "add_log",
        click: () => this.addWorklog(employee_id),
      },
    ];
  }

  /**
   * Generates the HTML content for the worklog section of the dialog.
   * @returns {string} - The HTML content for the worklog section.
   */
  getWorklogSectionHTML() {
    return `<div class="d-flex justify-between">
                <label id="worklog_section_label">${__("Add Worklog")}</label>
                <button class="btn btn-outline-info btn-xs edit-full-form-btn">${__(
                  "Enter complete detail"
                )}
                    &nearr;
                </button>
            </div>
            `;
  }

  /**
   * Updates the dialog UI based on the selected action.
   * If "End of work" is selected and no worklogs exist, disables the submit button.
   */
  updateDialogBasedOnAction() {
    let action_value = this.dialogUI.get_value("action");
    const isEndOfWork = action_value === "End of work";
    const isIncompleteCheckout = isEndOfWork && !this.hasWorklogs;

    this.dialogUI.get_primary_btn().prop("disabled", isIncompleteCheckout);
    this.dialogUI.get_field("worklog_section").$wrapper.toggle(isEndOfWork);

    if (this.hasWorklogs) {
      this.dialogUI.$wrapper
        .find("label#worklog_section_label")
        .removeClass("not-filled");
      this.dialogUI.$wrapper
        .find("label#worklog_section_label")
        .addClass("filled");
      this.dialogUI.$wrapper
        .find('button[data-fieldname="add_log"]')
        .removeClass("not-filled");
      this.dialogUI.$wrapper
        .find('button[data-fieldname="add_log"]')
        .addClass("filled");
    } else {
      this.dialogUI.$wrapper
        .find("label#worklog_section_label")
        .addClass("not-filled");
      this.dialogUI.$wrapper
        .find("label#worklog_section_label")
        .removeClass("filled");
      this.dialogUI.$wrapper
        .find('button[data-fieldname="add_log"]')
        .addClass("not-filled");
      this.dialogUI.$wrapper
        .find('button[data-fieldname="add_log"]')
        .removeClass("filled");
    }
  }

  /**
   * Initializes the dialog with necessary UI adjustments and event bindings.
   */
  initializeDialog() {
    this.dialogUI
      .get_field("add_log")
      .$wrapper.addClass("absolute-bottom-right");
    this.dialogUI.$wrapper
      .find(".edit-full-form-btn")
      .click(() => frappe.new_doc("Worklog"));
    this.dialogUI.$wrapper
      .find('button[data-fieldname="add_log"]')
      .addClass(this.hasWorklogs ? "filled" : "not-filled");
    this.dialogUI.$wrapper
      .find("label#worklog_section_label")
      .addClass(this.hasWorklogs ? "filled" : "not-filled");

    if (this.dialogUI.get_value("action") === "End of work")
      this.dialogUI
        .get_primary_btn()
        .prop("disabled", this.hasWorklogs ? false : true);
  }

  /**
   * Submits the check-in action for the employee and updates the dashboard.
   * @param {Object} values - The selected action and other dialog values.
   * @param {string} employee_id - The ID of the employee.
   */
  submitCheckin(values, employee_id) {
    frappe.call({
      method: "hr_time.api.flextime.api.submit_easy_checkin",
      args: {
        action: values.action,
        employee_id: employee_id,
      },
      callback: (response) => {
        this.refresh_dashboard();
        EasyCheckinStatus.render();
        this.preload();

        let message = "Successfully checked in";

        switch (values.action) {
          case "Break":
            message = "Successfully checked out for Break";
            break;
          case "End of work":
            message = "Successfully checked out for End of Work";
            break;
        }

        this.dialogUI.hide();

        frappe.show_alert(
          {
            message: __(message),
            indicator: "green",
          },
          5
        );
      },
    });
  }

  /**
   * Adds a new worklog entry for the employee.
   * @param {string} employee_id - The ID of the employee.
   */
  addWorklog(employee_id) {
    const worklog_text = this.dialogUI.get_value("worklog_box");
    if (!worklog_text.trim()) {
      frappe.show_alert(__("Worklog description cannot be empty"));
      return;
    }

    frappe.call({
      method: "hr_time.api.worklog.api.create_worklog",
      args: {
        employee_id: employee_id,
        worklog_text: worklog_text,
      },
      callback: (response) => {
        const res = response.message;
        if (res.status == "error") {
          frappe.show_alert(
            {
              message: __(res.message),
              indicator: "red",
            },
            5
          );
        } else {
          frappe.show_alert(
            {
              message: __("Worklog added successfully"),
              indicator: "green",
            },
            5
          );
          this.hasWorklogs = true;
          this.updateDialogBasedOnAction();
        }
      },
    });
  }

  /**
   * Refreshes the dashboard UI by triggering the refresh action on the associated buttons.
   */
  refresh_dashboard() {
    if (this.refresh_buttons === undefined) {
      return;
    }

    for (let button of this.refresh_buttons) {
      button.click();
    }
  }

  /**
   * Binds events for number card of dashboard
   */
  static prepare_dashboard() {
    let dialog = EasyCheckinDialog.singleton();

    document
      .getElementById("hr_time_number_card_checkin_status")
      .querySelector(".checkin_status").onclick = function () {
      dialog.show();
    };

    dialog.refresh_buttons = [
      document
        .querySelector('[number_card_name="Checkin status"]')
        .querySelector('[data-action="action-refresh"]'),
      document
        .querySelector('[number_card_name="Employees present"]')
        .querySelector('[data-action="action-refresh"]'),
      document
        .querySelector('[quick_list_name="Employee Checkin"]')
        .querySelector(".refresh-list.btn"),
    ];

    setTimeout(() => {
      dialog.refresh_dashboard();
    }, 15000);
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
