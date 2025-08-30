/**
 * @fileoverview Utility file defining messages to be shown to the user in UI.
 * @module HR_TIME_MANAGEMENT
 */

const MESSAGES = {   
  FAILED_PRELOAD_CHECKIN_OPTIONS: "Failed to preload check-in options",
  NOT_FOUND_EMPLOYEE: "No employee document found for the current user : Please ensure you are logged in as an employee.",
  NOT_FOUND_EMPLOYEE_ID: "No employee ID found for the current user : Please ensure you are logged in as an employee.",
  SUCCESS_BREAK: "Successfully checked out for Break",
  SUCCESS_RESUME: "Successfully resumed work",
  SUCCESS_CHECKOUT: "Successfully checked out for End of Work",
  SUCCESS_CHECKIN: "Successfully checked in",
  FAILED_CHECKOUT: "Could not Checkout of work",
  ERR_GET_EMPLOYEE_ID: "Error fetching employee ID",
  SUCCESS_WORKLOG_ADDITION: "Worklog added successfully",
  ERR_GET_WORKLOG_STATUS: "Error fetching worklog status",
  EMPTY_TASK_DESC_WHEN_WORKLOGS: "You have no Worklogs today : Task description must not be empty.",
  ALERT_NO_WORKLOG:"No worklog entered for today",
  ALERT_YES_WORKLOG:"Worklog has already been entered for today",
  UNKNOWN_ACTION: "Unknown action provided",
  ERR_LOG_IN_FUTURE: "The entered time cannot be in the future",
  WARN_NO_HOME_OFFICE: "Please specify 'Home Office' status",
  WARN_NO_EMP_ID: "Employee ID is required"
}

export default MESSAGES;