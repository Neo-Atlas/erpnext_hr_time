class Messages:
    class Employee:
        NOT_FOUND_EMPLOYEE_ID = (
            "No employee ID found for the current user : "
            "Please ensure you are logged in as an employee"
        )
        NOT_FOUND_EMPLOYEE = "No Employee record found for the current user."
        SUCCESS_FOUND = "Employee found successfully."

    class Worklog:
        SUCCESS_SAVED = "Worklog saved"
        SUCCESS_WORKLOG_AND_CHECKOUT = "Worklog saved and checked out successfully."
        EMPTY_EMPLOYEE = "Employee field must not be empty"
        ERR_CREATE_WORKLOG_FUTURE_TIME = "Log time cannot be in the future."
        ERR_NO_WORK_TIME = "You have no work time recorded today. Please try again after some checkin time."
        NO_WORK_DESC = "Please add work description before checking out."
        NO_HOME_OFFICE = "Please specify if you worked from home."
        ERR_NO_TASK_ALLOCATIONS = "Please allocate time to tasks before saving!"
        ERR_ALLOCATION_MISMATCH_EXCEEDS = (
            "You have {0} hrs left to allocate. This exceeds the ±{1} hr tolerance. "
            "Please adjust your allocations."
        )
        ERR_ALLOCATION_EXCEEDS_WORKED = "You have allocated {0} hrs more than worked. This exceeds ±{1} hr tolerance."

    class Timesheet:
        SUCCESS_TIMESHEET_PROCESSED = "Timesheet processed successfully."
        DEFAULT_UNALLOCATED_DESCRIPTION = "Unallocated time from the allocated tasks"

    class Checkin:
        SUCCESS_BREAK = "Successfully checked out for Break."
        SUCCESS_CHECKOUT = "Successfully checked out for End of Work."
        SUCCESS_CHECKIN = "Successfully checked in."
        SUCCESS_RESUME = "Work resumed"
        FAILED_CHECKOUT_DUE_TO_NO_WORKLOGS = "Could not Checkout of work : You have no Worklogs today."

    class Common:
        UNKNOWN_ACTION = "Unknown action provided."
        ERR_UNKNOWN = "An unexpected error occurred. Please try again."
        ERR_DB_CONN = "Database connection failed"
        ERR_DB = "Database error."
        ERR_UNEXPECTED_RESPONSE = "Received an unexpected response from server."
        ERR_BACKEND_UNREACHABLE = "Cannot connect to server. Please check your network connection."

    # Titles (for modals/dialogs)
    class Titles:
        WARNING = "Warning"
        ERROR = "Error"
        SUCCESS = "Success"
        INFO = "Information"
        NO_WORK_TIME = "No Work Time Recorded"
        NO_TASK_ALLOCATIONS = "No Task Allocations"
        MISSING_EMPLOYEE = "Missing Employee"
        MISSING_HOME_OFFICE = "Missing Home Office"
        UNDER_ALLOCATED = "Under-allocated"
        OVER_ALLOCATED = "Over-allocated"
        ALLOCATION_MISMATCH = "Allocation Mismatch"
        NO_WORK_DESC = "Missing Work Description"
        INVALID_TIME = "Invalid Log Time"
