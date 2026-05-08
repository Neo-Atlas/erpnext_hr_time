/**
 * @fileoverview Utility class for Frappe-specific wrappers and helpers.
 *
 * @module FrappeUtils
 */


export class FrappeUtils{
  /**
   * Time duration (in seconds) until which the message is visible to User.
   */
  static DEFAULT_DIALOG_DURATION = 4

  /**
   * Fixed set of available indicator colors (in Frappe's UI dialogs).
   */
  static INDICATOR_COLORS = {
    BLUE: "blue",
    GREEN: "green",
    ORANGE: "orange",
    RED: "red",
    YELLOW: "yellow"
  }

  /**
   * Displays a warning message to the user (modal dialog)..
   * 
   * @param {string} msg - The message to be warned with.
   * @param {string} title - Optional custom title (defaults to "WARNING").
   */
  static warn_user = (msg, title = "WARNING") => {    
    frappe.msgprint(
      {
        title: frappe._(title),
        message: frappe._(msg),
        indicator: FrappeUtils.INDICATOR_COLORS.ORANGE,
      }
    );
  }

  /**
   * Displays an error message to the user (modal dialog).
   * 
   * @param {string} msg - The error message to display.
   * @param {string} title - Optional custom title (defaults to "ERROR").
   */
  static error_modal = (msg, title = "ERROR") => {
    frappe.msgprint({
      title: frappe._(title),
      message: frappe._(msg),
      indicator: FrappeUtils.INDICATOR_COLORS.RED,
    });
  }

  /**
   * Displays an info message to the user (modal dialog).
   * 
   * @param {string} msg - The info message to display.
   * @param {string} title - Optional custom title (defaults to "INFO").
   */
  static info_modal = (msg, title = "INFO") => {
    frappe.msgprint({
      title: frappe._(title),
      message: frappe._(msg),
      indicator: FrappeUtils.INDICATOR_COLORS.BLUE,
    });
  }

  /**
   * Displays a success message to the user (modal dialog).
   * 
   * @param {string} msg - The success message to display.
   * @param {string} title - Optional custom title (defaults to "SUCCESS").
   */
  static success_modal = (msg, title = "SUCCESS") => {
    frappe.msgprint({
      title: frappe._(title),
      message: frappe._(msg),
      indicator: FrappeUtils.INDICATOR_COLORS.GREEN,
    });
  }

  /**
   * Displays a warning toast notification (auto-dismiss).
   * 
   * @param {string} msg - The message to display.
   * @param {number} duration - Duration in seconds (defaults to DEFAULT_DIALOG_DURATION).
   */
  static toast_warning = (msg, duration = FrappeUtils.DEFAULT_DIALOG_DURATION) => {
    frappe.show_alert({
      message: frappe._(msg),
      indicator: FrappeUtils.INDICATOR_COLORS.ORANGE,
    }, duration);
  }

  /**
   * Displays an informational message to the user for general scenarios.
   * 
   * @param {string} msg - The information message to be displayed.
   * @param {number} duration - Duration in seconds (defaults to DEFAULT_DIALOG_DURATION).
   */
  static toast_info = (msg, duration = FrappeUtils.DEFAULT_DIALOG_DURATION)=>{
    frappe.show_alert(
      {
        message: frappe._(msg),
        color: FrappeUtils.INDICATOR_COLORS.BLUE
      }, duration);
  }

  /**
   * Displays a success message to the user.
   * 
   * @param {string} msg - The success message to be displayed.
   * @param {number} duration - Duration in seconds (defaults to DEFAULT_DIALOG_DURATION).
   */
  static toast_success = (msg, duration = FrappeUtils.DEFAULT_DIALOG_DURATION)=>{    
    frappe.show_alert({
      message: frappe._(msg),
      indicator: FrappeUtils.INDICATOR_COLORS.GREEN,
    }, duration);
  }

  /**
   * Displays a failure message to the user.
   * 
   * @param {string} msg - The failure message to be displayed.
   * @param {number} duration - Duration in seconds (defaults to DEFAULT_DIALOG_DURATION).
   */
  static toast_failure = (msg, duration = FrappeUtils.DEFAULT_DIALOG_DURATION)=>{    
    frappe.show_alert({
      message: frappe._(msg),
      indicator: FrappeUtils.INDICATOR_COLORS.RED,
    }, duration);
  }

  /**
   * Throws an error message using Frappe's throw method.
   * 
   * @param {string} msg - The error message to be thrown.
   * @param {ErrorConstructor} [errorType=Error] - The constructor of the error to be thrown. 
   *                                                Defaults to the generic Error.
   */
  static throw_error_msg = (msg, errorType = Error) => {
    frappe.throw(frappe._(msg), errorType);
  }

  /**
   * Return date time in DB format (YYYY-MM-DD hh:mm:ss.ffffff)
   * 
   * @param {Date} date - The Date instance to format.
   * 
   * @returns {string}
   */
  static get_db_format_time = (date)=>{
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    const milliseconds = String(date.getMilliseconds()).padStart(3, '0') + '000'; // Convert to 6 digits
    
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}.${milliseconds}`;
  }
}