class Messages:
    class Employee:
        NOT_FOUND_EMPLOYEE_ID = "No employee ID found for the current user: Please ensure you are logged in."
        NOT_FOUND_EMPLOYEE = "No Employee record found for the current user."

    class Worklog:
        SUCCESS_WORKLOG_ADDITION = "Worklog added successfully."
        SUCCESS_WORKLOG_CREATION = "Worklog created successfully."
        ERR_GET_WORKLOG_STATUS = "Error fetching worklog status."
        ERR_CREATE_WORKLOG = "Worklog Creation Error"
        EMPTY_TASK_DESC = "Task description must not be empty."
        EMPTY_TASK_DESC_WHEN_WORKLOGS = "You have no Worklogs today: Task description must not be empty."

    class Checkin:
        SUCCESS_BREAK = "Successfully checked out for Break."
        SUCCESS_CHECKOUT = "Successfully checked out for End of Work."
        SUCCESS_CHECKIN = "Successfully checked in."
        FAILED_CHECKOUT = "Could not Checkout of work."
        FAILED_CHECKOUT_DUE_TO_NO_WORKLOGS = "Could not Checkout of work : You have no Worklogs today."

    class Flextime:
        pass

    class Common:
        UNKNOWN_ACTION = "Unknown action provided."
        ERR_DB = "Database error."
