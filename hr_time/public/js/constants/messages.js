/**
 * @fileoverview Utility file defining messages to be shown to the user in UI.
 * @module HR_TIME_MANAGEMENT
 */

const MESSAGES = {
  // Generic warnings
  NO_EDIT: "Cannot Edit",
  REDIRECT_HOME: "Redirecting to home",
  ERR_BACKEND_UNREACHABLE: "Cannot connect to server. Please check your network connection.",
  ERR_NO_DATA_RECEIVED: "No data received from server.",
  
  // Checkin dialog messages
  FAILED_PRELOAD_CHECKIN_OPTIONS: "Failed to preload check-in options",

  // Worklog form validation messages
  WARN_NO_MODIFY_WORKLOG: 'This worklog is historical and cannot be modified.', 
  ERR_NO_WORK_TIME: "You have no work time recorded today. Please try again after some checkin time.",
  ERR_NO_EMPLOYEE: "Employee not found.",
  EMPTY_WORK_DESC_WHEN_WORKLOG_EXISTS: "Please add work description before checking out.",
  EMPTY_WORK_DESC_WHEN_NO_WORKLOGS: "You have no Worklogs today : Work summary must not be empty.",

  // Info messages
  INFO_OPENING_EXISTING: "Opening existing worklog for today",

  // Titles for modals
  TITLE_NO_WORK_TIME: "No Work Time Recorded",

  // Confirm messages
  CONFIRM_SAVE_AND_CHECKOUT: "Save current worklog and checkout? This will capture your ongoing session and end your work day."
}

export default MESSAGES;