/**
 * @fileoverview Utility file defining messages to be shown to the user in UI.
 * @module HR_TIME_MANAGEMENT
 */

const MESSAGES = {
  // Checkin dialog messages
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
  WARN_NO_EMP_ID: "Employee ID is required",

  // Worklog form validation messages
  ERR_NO_WORK_TIME: "You have no work time recorded today. Please check in first.",
  ERR_NO_TASK_ALLOCATIONS: "Please allocate time to tasks before checking out.",
  ERR_MISSING_EMPLOYEE: "Employee not found. Please reload the form.",
  ERR_MISSING_HOME_OFFICE: "Please specify if you worked from home.",
  ERR_UNDER_ALLOCATED: "You have {0} hrs left to allocate. This exceeds the ±{1} hr tolerance. Please adjust your allocations.",
  ERR_OVER_ALLOCATED: "You have allocated {0} hrs more than you worked. This exceeds the ±{1} hr tolerance. Please adjust your allocations.",

  // Success messages
  SUCCESS_WORKLOG_SAVED: "Worklog saved and checked out successfully.",
  SUCCESS_WORKLOG_CREATED: "Worklog created successfully.",
  SUCCESS_WORKLOG_UPDATED: "Worklog updated successfully.",

  // Info messages
  INFO_OPENING_EXISTING: "Opening existing worklog for today",

  // Titles for modals
  TITLE_WARNING: "Warning",
  TITLE_ERROR: "Error",
  TITLE_SUCCESS: "Success",
  TITLE_INFO: "Information",
  TITLE_NO_WORK_TIME: "No Work Time Recorded",
  TITLE_NO_TASK_ALLOCATIONS: "No Task Allocations",
  TITLE_MISSING_EMPLOYEE: "Missing Employee",
  TITLE_MISSING_HOME_OFFICE: "Missing Home Office",
  TITLE_UNDER_ALLOCATED: "Under-allocated",
  TITLE_OVER_ALLOCATED: "Over-allocated",
  TITLE_ALLOCATION_MISMATCH: "Allocation Mismatch",

  // Confirm messages
  CONFIRM_SAVE_AND_CHECKOUT: "Save current worklog and checkout? This will capture your ongoing session and end your work day."
}

export default MESSAGES;