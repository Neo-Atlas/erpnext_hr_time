import { EasyCheckinStatus } from "./easy_checkin_status";
import { warn_user, alert_success, alert_failure, throw_error_msg } from './utils/frappe_utils'
import { fetchCurrentEmployeeId, fetchWorklogStatus } from "./api/flextime.api";
import MESSAGES from "./constants/messages.json";

/**
 * Class representing the EasyCheckinDialog for managing employee check-ins.
 */
export class EasyCheckinDialog {
  /** 
   * Fixed text definitions for various labels in the Dialog
   * @type {Object<string, string>}
   */
  static LABELS = {
    TITLE: "Checkin",
    PRIMARY_ACTION_BTN: "Submit",
    PLACEHOLDER_WORKLOG_TASK_DESC: 'Describe your task here'
  }

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
   * Reference to the Frappe's dialog UI instance.
   * @type {Object}
   */
  dialogUI;

  /**
   * Array of buttons to refresh the dashboard UI.
   * @type {Array<Element>}
   */
  refresh_buttons;

  /**
   * Interval duration (in milliseconds) to refresh the dashboard in.
   */
  static REFRESH_DASHBOARD_INTERVAL = 15000;

  /**
   * Predefined Action options for Checkin events
   */
  static ACTIONS = {
    EOW: 'End of work',
    BRK: 'Break',
    SOW: 'Start of work'
  };

  /**
   * Preloads the current checkin status
   */
  async preloadCheckinOptions() {
    try {
      const response = await frappe.call({
        method: "hr_time.api.flextime.api.get_easy_checkin_options",
      });
      this.options = response.message.options;
      this.default = response.message.default;
    } catch (error) {
      console.error(`${MESSAGES.FAILED_PRELOAD_CHECKIN_OPTIONS}" : ${error}`);
    }
  }

  /** 
   * Utility method to check if a Checkin dialog is already open
   */
  isCheckinDialogOpen() {
    return $(".modal:visible").filter(function() {
      return $(this).find(".modal-title").text().trim() === EasyCheckinDialog.LABELS.TITLE;
    }).length > 0;
  }

  /**
   * Initiates Checkin dialog creation after fetching current employee's ID.
   */
  async show() {
    try{
      const employee_id = await fetchCurrentEmployeeId()
      this.checkWorklogsThenCreateDialog(employee_id); // Call the next step if employee ID is available
    }catch(error){
      throw_error_msg(MESSAGES.NOT_FOUND_EMPLOYEE_ID); // Show error message if no employee ID
      console.error(`${MESSAGES.ERR_GET_EMPLOYEE_ID} : ${error}`);
    }
  }

  /**
   * Checks if the employee has worklogs for today using the provided employee ID, then creates Checkin dialog.
   * @param {string} employee_id - The ID of the employee to check worklogs for.
   */
  async checkWorklogsThenCreateDialog(employee_id) {
    try{
      const hasWorklogs = await fetchWorklogStatus(employee_id)
      this.hasWorklogs = hasWorklogs
      this.createCheckinDialog(employee_id);
    }catch(error){
      console.error(`${MESSAGES.ERR_GET_WORKLOG_STATUS}: ${error}`);
    };
  }

  /**
   * Creates and displays the check-in dialog with options and actions.
   * @param {string} employee_id - The ID of the employee to create Checkin actions for.
   */
  createCheckinDialog(employee_id) {
    this.dialogUI = new frappe.ui.Dialog({
      title: __(EasyCheckinDialog.LABELS.TITLE),
      fields: this.getDialogFields(employee_id),
      size: "small",
      primary_action_label: __(EasyCheckinDialog.LABELS.PRIMARY_ACTION_BTN, undefined, "checkin"),
      primary_action: (values) => {
        const actionValue = values.action;
        const worklog_text = this.dialogUI.get_value("worklog_box")
        const trimmed_worklog_text = worklog_text ? worklog_text.trim() : '';
      
        // Submit only Checkin for actions other than 'End of work' OR if 'Task Description' is empty when Checking out
        if(actionValue !== EasyCheckinDialog.ACTIONS.EOW || !trimmed_worklog_text){
          if (actionValue === EasyCheckinDialog.ACTIONS.EOW && !this.hasWorklogs) {
            warn_user(MESSAGES.EMPTY_TASK_DESC_WHEN_WORKLOGS);
            return;
          }
          this.submitCheckin(values, employee_id);
        }else{
          this.submitCheckinAfterAddingWorklog(values, employee_id, trimmed_worklog_text);
        }
      }
    });

    this.initializeDialog(employee_id);
  }

  /**
   * Returns the configuration of fields to be displayed in the check-in dialog.
   * @returns {Array<Object>} - The fields configuration for Frappe's UI dialog.
   * @param {string} employee_id - The ID of the employee
   */
  getDialogFields(employee_id) {
    return [
      {
        label: "Action",
        fieldname: "action",
        fieldtype: "Select",
        options: this.options,
        default: this.default,
        change: () => this.updateDialogBasedOnAction(employee_id),
      },
      {
        fieldtype: "Section Break",
        depends_on: `eval: doc.action === '${EasyCheckinDialog.ACTIONS.EOW}'`,
      },
      {
        fieldname: "worklog_section",
        fieldtype: "HTML",
      },
      {
        fieldname: "worklog_box",
        fieldtype: "Text",
        placeholder: __(EasyCheckinDialog.LABELS.PLACEHOLDER_WORKLOG_TASK_DESC) + " 🖉",
        depends_on: `eval: doc.action === '${EasyCheckinDialog.ACTIONS.EOW}'`,
      }
    ];
  }


  /**
   * Updates the dialog UI based on the selected action & Worklog status.
   * @param {string} employee_id - The ID of the current employee.
   */
  updateDialogBasedOnAction(employee_id) {
    const action_value = this.dialogUI.get_value("action");
    const isEndOfWork = action_value === EasyCheckinDialog.ACTIONS.EOW;

    if(isEndOfWork){
      fetchWorklogStatus(employee_id)
      .then((hasWorklogs) => {
        this.hasWorklogs = hasWorklogs
        this.dialogUI.$wrapper.find("label#worklog_section_label")
          .toggleClass("filled", this.hasWorklogs)
          .toggleClass("not-filled", !this.hasWorklogs);
      })
      .catch((error) => {
        console.error(`${MESSAGES.ERR_GET_WORKLOG_STATUS}: ${error}`);
      });
    }
  }

  /**
   * Initializes the dialog with necessary UI adjustments and event bindings if one is not rendered.
   * @param {string} employee_id - The ID of the current employee.
   */
  initializeDialog(employee_id) {
    // Stop re-initialization of dialog UI if one is already open
    if(this.isCheckinDialogOpen()) return;
    
    this.dialogUI.show();
    
    // Fetch the worklog section's label HTML from the API
    frappe.call({
      method: "hr_time.api.worklog.api.render_worklog_header",
      callback: (response) => {
        if (response.message) {
          const worklog_section = this.dialogUI.get_field("worklog_section");
          if (worklog_section) {
            // Set the rendered HTML to the worklog_section field
            worklog_section.$wrapper.html(response.message);
            this.dialogUI.$wrapper
              .find(".edit-full-form-btn")
              .click(() => frappe.new_doc("Worklog"));
            this.updateDialogBasedOnAction(employee_id);
          }
        }
      }
    });
  }

  /**
   * Submits the check-in action for the employee and updates the dashboard.
   * @param {Object} values - The selected action and other dialog values.
   * @param {string} employee_id - The ID of the current employee.
   */
  submitCheckin(values, employee_id) {
    frappe.call({
      method: "hr_time.api.flextime.api.submit_easy_checkin",
      args: {
        action: values.action,
        employee_id: employee_id,
      },
      callback: (response) => {
        // Exit early if there is an error in the response
        if (response && typeof response.message === 'object' && response.message.status === 'error') {
          alert_failure(response.message.message)
          return;
        }

        this.refresh_dashboard();
        EasyCheckinStatus.render();
        this.preloadCheckinOptions();   // Preload Checkin Options in the background

        let message;

        // Check the action and set the appropriate message
        switch (values.action) {
          case EasyCheckinDialog.ACTIONS.BRK:
            console.log('here');
            
            message = MESSAGES.SUCCESS_BREAK;
            break;
          case EasyCheckinDialog.ACTIONS.EOW:
            message = MESSAGES.SUCCESS_CHECKOUT;
            break;
          case EasyCheckinDialog.ACTIONS.SOW:
            message = MESSAGES.SUCCESS_CHECKIN;
            break;
          default:
            return; // Exit if none of the expected actions match
        }
        // Hide the dialog and show a success alert
        this.dialogUI.hide();
        alert_success(message);
      },
    });
  }

  /**
   * Adds a new worklog entry for the employee.
   * @param {string} employee_id - The ID of the current employee.
   */
  submitCheckinAfterAddingWorklog(values, employee_id, worklog_text) {
    frappe.call({
      method: "hr_time.api.worklog.api.create_worklog",
      args: {
        employee_id: employee_id,
        worklog_text: worklog_text,
      },
      callback: (response) => {
        if (response &&  response.message && typeof response.message === 'object') {
          const { status, message: resMessage } = response.message;

          if(typeof status === 'string' && status !== "success"){
            alert_failure(resMessage);
            alert_failure(MESSAGES.FAILED_CHECKOUT);
          }else {
            alert_success(MESSAGES.SUCCESS_WORKLOG_ADDITION)
            this.hasWorklogs = true;
            this.submitCheckin(values, employee_id);
          }
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
    }, EasyCheckinDialog.REFRESH_DASHBOARD_INTERVAL);
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
