/**
 * @fileoverview Utility class with (wrapper) methods for Frappe's messaging methods - to display (translatable)
*                alerts and messages in the application. * 
 * @module FrappeUtils
 */


export class FrappeUtils{
  /**
   * Time duration (in seconds) until which the message is visible to User.
   */
  static DEFAULT_DIALOG_DURATION = 5

  /**
   * Fixed set of available indicator colors (in Frappe's UI dialogs).
   */
  static INDICATOR_COLORS = {
    BLUE: "blue",
    GREEN: "green",
    ORANGE: "orange",
    RED: "red",
  }

  /**
   * Displays a warning message to the user.
   * 
   * @param {string} msg - The message to be warned with.
   */
  static warn_user = (msg) => {
    frappe.msgprint(
      {
        title: __("WARNING"),
        message: __(msg),
        indicator: FrappeUtils.INDICATOR_COLORS.ORANGE,
      }
    );
  } 

  /**
   * Displays an informational message to the user for general scenarios.
   * 
   * @param {string} msg - The information message to be displayed.
   */
  static alert_info = (msg)=>{
    frappe.show_alert(
      {
        title: __("MESSAGE"),
        message: __(msg),
        color: FrappeUtils.INDICATOR_COLORS.BLUE
      },
      FrappeUtils.DEFAULT_DIALOG_DURATION
    );
  }

  /**
   * Displays a success message to the user.
   * 
   * @param {string} msg - The success message to be displayed.
   */
  static alert_success = (msg)=>{
    frappe.show_alert(
      {
        title: __("SUCCESS"),
        message: __(msg),
        indicator: FrappeUtils.INDICATOR_COLORS.GREEN,
      },
      FrappeUtils.DEFAULT_DIALOG_DURATION
    );
  }

  /**
   * Displays a failure message to the user.
   * 
   * @param {string} msg - The failure message to be displayed.
   */
  static alert_failure = (msg)=>{
    frappe.show_alert(
      {
        title: __("FAILURE"),
        message: __(msg),
        indicator: FrappeUtils.INDICATOR_COLORS.RED,
      },
      FrappeUtils.DEFAULT_DIALOG_DURATION
    );
  }

  /**
   * Throws an error message using Frappe's throw method.
   * 
   * @param {string} msg - The error message to be thrown.
   * @param {Error} [errorType=Error] - The type of error to be thrown. Defaults to the generic Error.
   */
  static throw_error_msg = (msg, errorType = Error) => {
    frappe.throw(__(msg), errorType);
  };
}