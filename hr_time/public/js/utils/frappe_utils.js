/**
 * @fileoverview Utility functions for displaying alerts and messages in the application. * 
 * @module FrappeUtils
 */

/**
 * Time duration (in seconds) until which the message is visible to User.
 */
const DEFAULT_DIALOG_DURATION = 5

/**
 * Displays a warning message to the user.
 * 
 * @param {string} msg - The message to be warned with.
 */
const warn_user = (msg) => {
  frappe.msgprint(
    {
      title: __("WARNING"),
      message: __(msg),
      indicator: "orange",
    }
  );
} 

/**
 * Displays an informational message to the user for general scenarios.
 * 
 * @param {string} msg - The information message to be displayed.
 */
const alert_info = (msg)=>{
  frappe.show_alert(
    {
      title: __("MESSAGE"),
      message: __(msg),
      color: "blue"
    },
    DEFAULT_DIALOG_DURATION
  );
}

/**
 * Displays a success message to the user.
 * 
 * @param {string} msg - The success message to be displayed.
 */
const alert_success = (msg)=>{
  frappe.show_alert(
    {
      title: __("SUCCESS"),
      message: __(msg),
      indicator: "green",
    },
    DEFAULT_DIALOG_DURATION
  );
}

/**
 * Displays a failure message to the user.
 * 
 * @param {string} msg - The failure message to be displayed.
 */
const alert_failure = (msg)=>{
  frappe.show_alert(
    {
      title: __("FAILURE"),
      message: __(msg),
      indicator: "red",
    },
    DEFAULT_DIALOG_DURATION
  );
}

/**
 * Throws an error message.
 * 
 * @param {string} msg - The error message to be thrown.
 */
const throw_error_msg = (msg)=>{
  frappe.throw(__(msg))
}

export {warn_user, alert_failure, alert_info, alert_success, throw_error_msg}